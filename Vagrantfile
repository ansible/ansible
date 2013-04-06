# -*- mode: ruby -*-
# vi: set ft=ruby :

#
# See hacking/VAGRANT.md for setup instructions
#

Vagrant.configure("2") do |config|
  config.vm.box = "precise64"

  config.vm.synced_folder ".", "/opt/ansible", :id => "vagrant-root"
  config.vm.provision :shell, :path => "hacking/vagrant-provision.sh"

  config.vm.provider :virtualbox do |vb|
    config.vm.box_url = "http://files.vagrantup.com/precise64.box"
  end

  config.vm.provider :vmware_fusion do |v|
    config.vm.box_url = "http://files.vagrantup.com/precise64_vmware_fusion.box"
  end
end
