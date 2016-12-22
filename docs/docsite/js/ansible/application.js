angular.module('ansibleApp', []).filter('moduleVersion', function() {
  return function(modules, version) {

    var parseVersionString = function (str) {
        if (typeof(str) != 'string') { return false; }
        var x = str.split('.');
        // parse from string or default to 0 if can't parse
        var maj = parseInt(x[0]) || 0;
        var min = parseInt(x[1]) || 0;
        var pat = parseInt(x[2]) || 0;
        return {
            major: maj,
            minor: min,
            patch: pat
        }
    }

    var vMinMet = function(vmin, vcurrent) {
        minimum = parseVersionString(vmin);
        running = parseVersionString(vcurrent);
        if (running.major != minimum.major)
            return (running.major > minimum.major);
        else {
            if (running.minor != minimum.minor)
                return (running.minor > minimum.minor);
            else {
                if (running.patch != minimum.patch)
                    return (running.patch > minimum.patch);
                else
                    return true;
            }
        }
    };

    var result = [];
    if (!version) {
      return modules;
    }
    for (var i = 0; i < modules.length; i++) {
      if (vMinMet(modules[i].version_added, version)) {
        result[result.length] = modules[i];
      }
    }

    return result;
  };
}).filter('uniqueVersion', function() {
  return function(modules) {
    var result = [];
    var inArray = function (needle, haystack) {
      var length = haystack.length;
      for(var i = 0; i < length; i++) {
        if(haystack[i] == needle) return true;
      }
      return false;
    }

    var parseVersionString = function (str) {
        if (typeof(str) != 'string') { return false; }
        var x = str.split('.');
        // parse from string or default to 0 if can't parse
        var maj = parseInt(x[0]) || 0;
        var min = parseInt(x[1]) || 0;
        var pat = parseInt(x[2]) || 0;
        return {
            major: maj,
            minor: min,
            patch: pat
        }
    }

    for (var i = 0; i < modules.length; i++) {
      if (!inArray(modules[i].version_added, result)) {
        // Some module do not define version
        if (modules[i].version_added) {
          result[result.length] = "" + modules[i].version_added;
        }
      }
    }

    result.sort(
      function (a, b) {
        ao = parseVersionString(a);
        bo = parseVersionString(b);
        if (ao.major == bo.major) {
          if (ao.minor == bo.minor) {
            if (ao.patch == bo.patch) {
              return 0;
            }
            else {
              return (ao.patch > bo.patch) ? 1 : -1;
            }
          }
          else {
            return (ao.minor > bo.minor) ? 1 : -1;
          }
        }
        else {
          return (ao.major > bo.major) ? 1 : -1;
        }
    });

    return result;
  };
});

