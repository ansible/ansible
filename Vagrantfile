Vagrant::Config.run do |config|
  config.vm.box     = "lucid32"
  config.vm.host_name = "ansible"

  config.vm.provision :ansible do |ansible|
    # point Vagrant at the location of your playbook you want to run
    ansible.playbook = "test/vagranttest.yml"

    # the Vagrant VM will be put in this host group change this should
    # match the host group in your playbook you want to test
    ansible.hosts = "devboxes"
  end
end
