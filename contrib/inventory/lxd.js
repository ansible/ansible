#!/usr/bin/env nodejs
module.exports = (function() {
'use strict';
const	Promise = require('bluebird'),
	Unirest = Promise.promisifyAll(require('unirest')),
	fs = require('fs'),
	os = require('os'),
	writeFile = Promise.promisify(fs.writeFile),
	mkdirp = Promise.promisify(require('mkdirp')),
	openssl = require('openssl-wrapper'),
	ini = require('ini'),
	JSONPath = require('jsonpath-plus'),
	path = require('path'),
	Readline = require('readline'),
	configAnsible = ini.parse(fs.readFileSync('./ansible.cfg', 'utf-8')),
	opensslAsync = Promise.promisify(openssl.exec),
	config = ini.parse(fs.readFileSync(path.join(process.env.ANSIBLE_HOME, 'contrib/inventory/lxd.ini'), 'utf-8')),
	ANSIBLE_REMOTE_TMP = configAnsible.defaults.remote_tmp.replace("~", os.homedir()),
	KEYDIR = path.join(ANSIBLE_REMOTE_TMP, "ssl"),
	CA_KEY = path.join(KEYDIR, "ca.key"),
	CA_CRT = path.join(KEYDIR, "ca.crt"),
	CLIENT_KEY = path.join(KEYDIR, "client.key"),
	CLIENT_CRT = path.join(KEYDIR, "client.crt"),
	CLIENT_CSR = path.join(KEYDIR, "client.csr");

var debug;

var getLxdHosts = function() {
	return new Promise(function(resolve, reject) {
		var parseConfigFile = function(inventoryFile) {
			return new Promise(function(resolve, reject) {
				var	lxdHosts = [];
				const lineReader = Readline.createInterface({ input: fs.createReadStream(inventoryFile)});
				lineReader.on('line', function(line) {
					if (line.includes('ansible_connection=lxd')) {
						lxdHosts.push(line.split(" ")[0]);
					}
				})
				.on('close', function() {
					resolve(lxdHosts);
				});
			});
		}
		var ansibleInventory = configAnsible.defaults.inventory.replace("~", os.homedir());
		if (fs.statSync(ansibleInventory).isDirectory()) {
			var inventoryReadPromises = [];
			fs.readdirSync(ansibleInventory).forEach(function(file) {

				if (! file.startsWith(".") && file.match(/^(.*\.(?!(orig|bak|ini|retry|pyc|pyo|js)$))?[^.]*$/i)) {
					inventoryReadPromises.push(parseConfigFile(path.join(ansibleInventory, file)));
				}
			})
			Promise.all(inventoryReadPromises).then(function(lxdHostsArrayFromDifferentInventories) { 
				var allLxdHostsFromAllInvetorySources = [];
				lxdHostsArrayFromDifferentInventories.forEach(function(array) {
					allLxdHostsFromAllInvetorySources = allLxdHostsFromAllInvetorySources.concat(array);
				});
				resolve(allLxdHostsFromAllInvetorySources);
			});
		} else {
			parseConfigFile(ansibleInventory).then(function(singleInventoryOfLxdHosts) { resolve(singleInventoryOfLxdHosts); });
		}
	});
}
var generateClientCertificate = function(host) {
	if (fs.existsSync(CLIENT_CRT) && fs.existsSync(CLIENT_KEY)) {
		return Promise.resolve("Client cert found.  Skipping certificate generation.");
	}
	var subj = "/C="+config.lxd.ssl_country+"/ST="+config.lxd.ssl_stateOrProvince+"/L="+config.lxd.ssl_locality+"/O="+config.lxd.ssl_organization+"/CN="+config.lxd.ssl_commonName;
	return new Promise(function(resolve, reject) {
		mkdirp(KEYDIR)
		.then(function() { return opensslAsync('genrsa', {des3: false, '4096': false}) })
		.then(function(buffer) { return writeFile(CA_KEY, buffer); }, function(error) { console.log("ERROR: " + error); })
		.then(function() { return opensslAsync('req', {new: true, x509: true, days: 3650, subj: subj, key: CA_KEY}) })
		.then(function(buffer) { return writeFile(CA_CRT, buffer); })
		.then(function() { return opensslAsync('genrsa', {des3: false, '4096': false}) })
		.then(function(buffer) { return writeFile(CLIENT_KEY, buffer); })
		.then(function() { return opensslAsync('req', {new: true, subj: subj, key: CLIENT_KEY}) })
		.then(function(buffer) { return writeFile(CLIENT_CSR, buffer); })
		.then(function() { return opensslAsync('x509', {req: true, days: 3650, in: CLIENT_CSR, CA: CA_CRT, CAkey: CA_KEY, set_serial: '01'}) })
		.then(function(buffer) { return writeFile(CLIENT_CRT, buffer); })
		.then(function(result) {
			console.log("Done generating self signed client cert.");
			resolve();
		})
		.catch(function(e) {
			reject("Error setting up client certificate: " + e);
		});
	});
}
var registerCertWithLXDHost = function(host) {
	return new Promise(function(resolve, reject) {
		var Request = Unirest.post('https://'+host+':8443/1.0/certificates')
		.headers({'Accept': 'application/json', 'Content-Type': 'application/json'});

		Request.options.cert = fs.readFileSync(CLIENT_CRT);
		Request.options.key = fs.readFileSync(CLIENT_KEY);

		Request.send({ "type": "client", "password": "8hJKBwMzxAycXf0CfVWy" })
		.end(function (response) {
			resolve(host);
		});
	});
}
process.env['NODE_TLS_REJECT_UNAUTHORIZED'] = '0';

var getContainers = function(host) {
	return new Promise(function(resolve, reject) {
			var Request = Unirest.get('https://'+host+':8443/1.0/containers');
			Request.options.cert = fs.readFileSync(CLIENT_CRT);
			Request.options.key = fs.readFileSync(CLIENT_KEY);
			Request.end(function (response) {
			  resolve(response.body);
			});
		});
}
var doRestCall = function(endpoint) {
	return new Promise(function(resolve, reject) {
		var Request = Unirest.get(endpoint);
		Request.options.cert = fs.readFileSync(CLIENT_CRT);
		Request.options.key = fs.readFileSync(CLIENT_KEY);
		Request.end(function (response) {
		  resolve(response.body);
		});
	});
}
var listOptionHandler = function(host) {
	return new Promise(function(resolve, reject) {
		registerCertWithLXDHost(host)
		.then(function() { return getContainers(host)})
		.then(function(response) {
			var containers = [];
			response.metadata.forEach(function(container) {
				var RESTcalls = [ doRestCall("https://"+host+':8443' + container), doRestCall("https://"+host+':8443' + container + "/state") ];
				containers.push(Promise.all(RESTcalls));
			});
			return Promise.all(containers).then(function() {
				var result = [];
				containers.forEach(function(container) {
					result.push(container.value());
				});
				return(result); 
			});
		})
		.then(function(restResponses) {
			return new Promise(function(resolve, reject) {
				var groups = JSONPath({json: restResponses, path: "*[*.metadata.config[user.ansible.group]]"});
				var uniqueGroups = groups.filter(function(element, index) {
					return groups.indexOf(element) == index;
				});
				if (uniqueGroups)
					resolve({restResponses: restResponses, groups: uniqueGroups});
			});
		})
		.then(function(restResponseDataObject) {
			var groups = restResponseDataObject.groups;
			var restResponses = restResponseDataObject.restResponses;
			console.log("{")
			console.log("\"_meta\": { \"hostvars\": {}},")
			groups.forEach(function(group, i2, groups) {
				process.stdout.write("\""+group+"\": {\n\"hosts\": [");
				restResponses.forEach(function(restResponse, index, restResponses) {
					var name = restResponse[0].metadata.name;
					var ipv4Address = JSONPath({json: restResponse[1], path: "*.network.eth0.addresses.[0].address"});
					if (JSONPath({json: restResponse[0], path: "*.config[user.ansible.group]"}) == group) {
						if ((restResponses.length-1) == index) {
							console.log("\""+host+":::"+name+"\"],");
							console.log("\"vars\": { \"ansible_connection\":\"lxd\"}");
						} else {
							process.stdout.write("\""+host+":::"+name+"\", ");
						}
					}
				});
				if ((groups.length-2) <= i2)
					console.log("}");
				else
					console.log("}, ");
			});
			console.log("}")
		})
		.finally(resolve());
	});
}
generateClientCertificate()
.then(function(restResponse) {
	var command = process.argv[2],
		debug = process.argv.find(function (element) {
			return (element === "--debug")
		})
	switch(command) {
	  case "--list":
	  	getLxdHosts()
	  	.then(function(hosts) {
	  		var hostsToInventory = [];
  			hosts.forEach(function(host) {
  				hostsToInventory.push(new Promise(function(resolve, reject) {
  					listOptionHandler(host)
  					.finally(function() { resolve(); });
  				}));
  			});
  			Promise.all(hostsToInventory)
  			.then(function() {});
			});
	  ;;
	  case "--host": console.log("Add this functionality!  https://github.com/june07/ansible.git");
	  ;;
	}
});
})();