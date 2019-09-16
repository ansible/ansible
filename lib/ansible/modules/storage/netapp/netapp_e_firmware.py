#!/usr/bin/python

# (c) 2016, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: netapp_e_firmware
version_added: "2.9"
short_description: NetApp E-Series manage firmware.
description:
    - Ensure specific firmware versions are activated on E-Series storage system.
author:
    - Nathan Swartz (@ndswartz)
extends_documentation_fragment:
    - netapp.eseries
options:
    nvsram:
        description:
            - Path to the NVSRAM file.
        type: str
        required: true
    firmware:
        description:
            - Path to the firmware file.
        type: str
        required: true
    wait_for_completion:
        description:
            - This flag will cause module to wait for any upgrade actions to complete.
        type: bool
        default: false
    ignore_health_check:
        description:
            - This flag will force firmware to be activated in spite of the health check.
            - Use at your own risk. Certain non-optimal states could result in data loss.
        type: bool
        default: false
"""
EXAMPLES = """
- name: Ensure correct firmware versions
  netapp_e_firmware:
    ssid: "1"
    api_url: "https://192.168.1.100:8443/devmgr/v2"
    api_username: "admin"
    api_password: "adminpass"
    validate_certs: true
    nvsram: "path/to/nvsram"
    bundle: "path/to/bundle"
    wait_for_completion: true
- name: Ensure correct firmware versions
  netapp_e_firmware:
    ssid: "1"
    api_url: "https://192.168.1.100:8443/devmgr/v2"
    api_username: "admin"
    api_password: "adminpass"
    validate_certs: true
    nvsram: "path/to/nvsram"
    firmware: "path/to/firmware"
"""
RETURN = """
msg:
    description: Status and version of firmware and NVSRAM.
    type: str
    returned: always
    sample:
"""
import os

from time import sleep
from ansible.module_utils import six
from ansible.module_utils.netapp import NetAppESeriesModule, create_multipart_formdata, request
from ansible.module_utils._text import to_native, to_text, to_bytes


class NetAppESeriesFirmware(NetAppESeriesModule):
    HEALTH_CHECK_TIMEOUT_MS = 120000
    REBOOT_TIMEOUT_SEC = 15 * 60
    FIRMWARE_COMPATIBILITY_CHECK_TIMEOUT_SEC = 60
    DEFAULT_TIMEOUT = 60 * 15       # This will override the NetAppESeriesModule request method timeout.

    def __init__(self):
        ansible_options = dict(
            nvsram=dict(type="str", required=True),
            firmware=dict(type="str", required=True),
            wait_for_completion=dict(type="bool", default=False),
            ignore_health_check=dict(type="bool", default=False))

        super(NetAppESeriesFirmware, self).__init__(ansible_options=ansible_options,
                                                    web_services_version="02.00.0000.0000",
                                                    supports_check_mode=True)

        args = self.module.params
        self.nvsram = args["nvsram"]
        self.firmware = args["firmware"]
        self.wait_for_completion = args["wait_for_completion"]
        self.ignore_health_check = args["ignore_health_check"]

        self.nvsram_name = None
        self.firmware_name = None
        self.is_bundle_cache = None
        self.firmware_version_cache = None
        self.nvsram_version_cache = None
        self.upgrade_required = False
        self.upgrade_in_progress = False
        self.module_info = dict()

        self.nvsram_name = os.path.basename(self.nvsram)
        self.firmware_name = os.path.basename(self.firmware)

    def is_firmware_bundled(self):
        """Determine whether supplied firmware is bundle."""
        if self.is_bundle_cache is None:
            with open(self.firmware, "rb") as fh:
                signature = fh.read(16).lower()

                if b"firmware" in signature:
                    self.is_bundle_cache = False
                elif b"combined_content" in signature:
                    self.is_bundle_cache = True
                else:
                    self.module.fail_json(msg="Firmware file is invalid. File [%s]. Array [%s]" % (self.firmware, self.ssid))

        return self.is_bundle_cache

    def firmware_version(self):
        """Retrieve firmware version of the firmware file. Return: bytes string"""
        if self.firmware_version_cache is None:

            # Search firmware file for bundle or firmware version
            with open(self.firmware, "rb") as fh:
                line = fh.readline()
                while line:
                    if self.is_firmware_bundled():
                        if b'displayableAttributeList=' in line:
                            for item in line[25:].split(b','):
                                key, value = item.split(b"|")
                                if key == b'VERSION':
                                    self.firmware_version_cache = value.strip(b"\n")
                            break
                    elif b"Version:" in line:
                        self.firmware_version_cache = line.split()[-1].strip(b"\n")
                        break
                    line = fh.readline()
                else:
                    self.module.fail_json(msg="Failed to determine firmware version. File [%s]. Array [%s]." % (self.firmware, self.ssid))
        return self.firmware_version_cache

    def nvsram_version(self):
        """Retrieve NVSRAM version of the NVSRAM file. Return: byte string"""
        if self.nvsram_version_cache is None:

            with open(self.nvsram, "rb") as fh:
                line = fh.readline()
                while line:
                    if b".NVSRAM Configuration Number" in line:
                        self.nvsram_version_cache = line.split(b'"')[-2]
                        break
                    line = fh.readline()
                else:
                    self.module.fail_json(msg="Failed to determine NVSRAM file version. File [%s]. Array [%s]." % (self.nvsram, self.ssid))
        return self.nvsram_version_cache

    def check_system_health(self):
        """Ensure E-Series storage system is healthy. Works for both embedded and proxy web services."""
        try:
            rc, request_id = self.request("health-check", method="POST", data={"onlineOnly": True, "storageDeviceIds": [self.ssid]})

            while True:
                sleep(1)

                try:
                    rc, response = self.request("health-check?requestId=%s" % request_id["requestId"])

                    if not response["healthCheckRunning"]:
                        return response["results"][0]["successful"]
                    elif int(response["results"][0]["processingTimeMS"]) > self.HEALTH_CHECK_TIMEOUT_MS:
                        self.module.fail_json(msg="Health check failed to complete. Array Id [%s]." % self.ssid)

                except Exception as error:
                    self.module.fail_json(msg="Failed to retrieve health check status. Array Id [%s]. Error[%s]." % (self.ssid, to_native(error)))
        except Exception as error:
            self.module.fail_json(msg="Failed to initiate health check. Array Id [%s]. Error[%s]." % (self.ssid, to_native(error)))

        self.module.fail_json(msg="Failed to retrieve health check status. Array Id [%s]. Error[%s]." % self.ssid)

    def embedded_check_compatibility(self):
        """Verify files are compatible with E-Series storage system."""
        self.embedded_check_nvsram_compatibility()
        self.embedded_check_bundle_compatibility()

    def embedded_check_nvsram_compatibility(self):
        """Verify the provided NVSRAM is compatible with E-Series storage system."""

        # Check nvsram compatibility
        try:
            files = [("nvsramimage", self.nvsram_name, self.nvsram)]
            headers, data = create_multipart_formdata(files=files)

            rc, nvsram_compatible = self.request("firmware/embedded-firmware/%s/nvsram-compatibility-check" % self.ssid,
                                                 method="POST", data=data, headers=headers)

            if not nvsram_compatible["signatureTestingPassed"]:
                self.module.fail_json(msg="Invalid NVSRAM file. File [%s]." % self.nvsram)
            if not nvsram_compatible["fileCompatible"]:
                self.module.fail_json(msg="Incompatible NVSRAM file. File [%s]." % self.nvsram)

            # Determine whether nvsram is required
            for module in nvsram_compatible["versionContents"]:
                if module["bundledVersion"] != module["onboardVersion"]:
                    self.upgrade_required = True

                # Update bundle info
                self.module_info.update({module["module"]: {"onboard_version": module["onboardVersion"], "bundled_version": module["bundledVersion"]}})

        except Exception as error:
            self.module.fail_json(msg="Failed to retrieve NVSRAM compatibility results. Array Id [%s]. Error[%s]." % (self.ssid, to_native(error)))

    def embedded_check_bundle_compatibility(self):
        """Verify the provided firmware bundle is compatible with E-Series storage system."""
        try:
            files = [("files[]", "blob", self.firmware)]
            headers, data = create_multipart_formdata(files=files, send_8kb=True)
            rc, bundle_compatible = self.request("firmware/embedded-firmware/%s/bundle-compatibility-check" % self.ssid,
                                                 method="POST", data=data, headers=headers)

            # Determine whether valid and compatible firmware
            if not bundle_compatible["signatureTestingPassed"]:
                self.module.fail_json(msg="Invalid firmware bundle file. File [%s]." % self.firmware)
            if not bundle_compatible["fileCompatible"]:
                self.module.fail_json(msg="Incompatible firmware bundle file. File [%s]." % self.firmware)

            # Determine whether upgrade is required
            for module in bundle_compatible["versionContents"]:

                bundle_module_version = module["bundledVersion"].split(".")
                onboard_module_version = module["onboardVersion"].split(".")
                version_minimum_length = min(len(bundle_module_version), len(onboard_module_version))
                if bundle_module_version[:version_minimum_length] != onboard_module_version[:version_minimum_length]:
                    self.upgrade_required = True

                    # Check whether downgrade is being attempted
                    bundle_version = module["bundledVersion"].split(".")[:2]
                    onboard_version = module["onboardVersion"].split(".")[:2]
                    if bundle_version[0] < onboard_version[0] or (bundle_version[0] == onboard_version[0] and bundle_version[1] < onboard_version[1]):
                        self.module.fail_json(msg="Downgrades are not permitted. onboard [%s] > bundled[%s]."
                                                  % (module["onboardVersion"], module["bundledVersion"]))

                # Update bundle info
                self.module_info.update({module["module"]: {"onboard_version": module["onboardVersion"], "bundled_version": module["bundledVersion"]}})

        except Exception as error:
            self.module.fail_json(msg="Failed to retrieve bundle compatibility results. Array Id [%s]. Error[%s]." % (self.ssid, to_native(error)))

    def embedded_wait_for_upgrade(self):
        """Wait for SANtricity Web Services Embedded to be available after reboot."""
        for count in range(0, self.REBOOT_TIMEOUT_SEC):
            try:
                rc, response = self.request("storage-systems/%s/graph/xpath-filter?query=/sa/saData" % self.ssid)
                bundle_display = [m["versionString"] for m in response[0]["extendedSAData"]["codeVersions"] if m["codeModule"] == "bundleDisplay"][0]
                if rc == 200 and six.b(bundle_display) == self.firmware_version() and six.b(response[0]["nvsramVersion"]) == self.nvsram_version():
                    self.upgrade_in_progress = False
                    break
            except Exception as error:
                pass
            sleep(1)
        else:
            self.module.fail_json(msg="Timeout waiting for Santricity Web Services Embedded. Array [%s]" % self.ssid)

    def embedded_upgrade(self):
        """Upload and activate both firmware and NVSRAM."""
        files = [("nvsramfile", self.nvsram_name, self.nvsram),
                 ("dlpfile", self.firmware_name, self.firmware)]
        headers, data = create_multipart_formdata(files=files)
        try:
            rc, response = self.request("firmware/embedded-firmware?staged=false&nvsram=true", method="POST", data=data, headers=headers)
            self.upgrade_in_progress = True
        except Exception as error:
            self.module.fail_json(msg="Failed to upload and activate firmware. Array Id [%s]. Error[%s]." % (self.ssid, to_native(error)))
        if self.wait_for_completion:
            self.embedded_wait_for_upgrade()

    def proxy_check_nvsram_compatibility(self):
        """Verify nvsram is compatible with E-Series storage system."""
        data = {"storageDeviceIds": [self.ssid]}
        try:
            rc, check = self.request("firmware/compatibility-check", method="POST", data=data)
            for count in range(0, int((self.FIRMWARE_COMPATIBILITY_CHECK_TIMEOUT_SEC / 5))):
                sleep(5)
                try:
                    rc, response = self.request("firmware/compatibility-check?requestId=%s" % check["requestId"])
                    if not response["checkRunning"]:
                        for result in response["results"][0]["nvsramFiles"]:
                            if result["filename"] == self.nvsram_name:
                                return
                        self.module.fail_json(msg="NVSRAM is not compatible. NVSRAM [%s]. Array [%s]." % (self.nvsram_name, self.ssid))
                except Exception as error:
                    self.module.fail_json(msg="Failed to retrieve NVSRAM status update from proxy. Array [%s]. Error [%s]." % (self.ssid, to_native(error)))
        except Exception as error:
            self.module.fail_json(msg="Failed to receive NVSRAM compatibility information. Array [%s]. Error [%s]." % (self.ssid, to_native(error)))

    def proxy_check_firmware_compatibility(self):
        """Verify firmware is compatible with E-Series storage system."""
        data = {"storageDeviceIds": [self.ssid]}
        try:
            rc, check = self.request("firmware/compatibility-check", method="POST", data=data)
            for count in range(0, int((self.FIRMWARE_COMPATIBILITY_CHECK_TIMEOUT_SEC / 5))):
                sleep(5)
                try:
                    rc, response = self.request("firmware/compatibility-check?requestId=%s" % check["requestId"])
                    if not response["checkRunning"]:
                        for result in response["results"][0]["cfwFiles"]:
                            if result["filename"] == self.firmware_name:
                                return
                        self.module.fail_json(msg="Firmware bundle is not compatible. firmware [%s]. Array [%s]." % (self.firmware_name, self.ssid))

                except Exception as error:
                    self.module.fail_json(msg="Failed to retrieve firmware status update from proxy. Array [%s]. Error [%s]." % (self.ssid, to_native(error)))
        except Exception as error:
            self.module.fail_json(msg="Failed to receive firmware compatibility information. Array [%s]. Error [%s]." % (self.ssid, to_native(error)))

    def proxy_upload_and_check_compatibility(self):
        """Ensure firmware is uploaded and verify compatibility."""
        try:
            rc, cfw_files = self.request("firmware/cfw-files")
            for file in cfw_files:
                if file["filename"] == self.nvsram_name:
                    break
            else:
                fields = [("validate", "true")]
                files = [("firmwareFile", self.nvsram_name, self.nvsram)]
                headers, data = create_multipart_formdata(files=files, fields=fields)
                try:
                    rc, response = self.request("firmware/upload", method="POST", data=data, headers=headers)
                except Exception as error:
                    self.module.fail_json(msg="Failed to upload NVSRAM file. File [%s]. Array [%s]. Error [%s]."
                                              % (self.nvsram_name, self.ssid, to_native(error)))

            self.proxy_check_nvsram_compatibility()

            for file in cfw_files:
                if file["filename"] == self.firmware_name:
                    break
            else:
                fields = [("validate", "true")]
                files = [("firmwareFile", self.firmware_name, self.firmware)]
                headers, data = create_multipart_formdata(files=files, fields=fields)
                try:
                    rc, response = self.request("firmware/upload", method="POST", data=data, headers=headers)
                except Exception as error:
                    self.module.fail_json(msg="Failed to upload firmware bundle file. File [%s]. Array [%s]. Error [%s]."
                                              % (self.firmware_name, self.ssid, to_native(error)))

                self.proxy_check_firmware_compatibility()
        except Exception as error:
            self.module.fail_json(msg="Failed to retrieve existing existing firmware files. Error [%s]" % to_native(error))

    def proxy_check_upgrade_required(self):
        """Staging is required to collect firmware information from the web services proxy."""
        # Verify controller consistency and get firmware versions
        try:
            # Retrieve current bundle version
            if self.is_firmware_bundled():
                rc, response = self.request("storage-systems/%s/graph/xpath-filter?query=/controller/codeVersions[codeModule='bundleDisplay']" % self.ssid)
                current_firmware_version = six.b(response[0]["versionString"])
            else:
                rc, response = self.request("storage-systems/%s/graph/xpath-filter?query=/sa/saData/fwVersion" % self.ssid)
                current_firmware_version = six.b(response[0])

            # Determine whether upgrade is required
            if current_firmware_version != self.firmware_version():

                current = current_firmware_version.split(b".")[:2]
                upgrade = self.firmware_version().split(b".")[:2]
                if current[0] < upgrade[0] or (current[0] == upgrade[0] and current[1] <= upgrade[1]):
                    self.upgrade_required = True
                else:
                    self.module.fail_json(msg="Downgrades are not permitted. Firmware [%s]. Array [%s]." % (self.firmware, self.ssid))
        except Exception as error:
            self.module.fail_json(msg="Failed to retrieve controller firmware information. Array [%s]. Error [%s]" % (self.ssid, to_native(error)))
        # Determine current NVSRAM version and whether change is required
        try:
            rc, response = self.request("storage-systems/%s/graph/xpath-filter?query=/sa/saData/nvsramVersion" % self.ssid)
            if six.b(response[0]) != self.nvsram_version():
                self.upgrade_required = True

        except Exception as error:
            self.module.fail_json(msg="Failed to retrieve storage system's NVSRAM version. Array [%s]. Error [%s]" % (self.ssid, to_native(error)))

    def proxy_wait_for_upgrade(self, request_id):
        """Wait for SANtricity Web Services Proxy to report upgrade complete"""
        if self.is_firmware_bundled():
            while True:
                try:
                    sleep(5)
                    rc, response = self.request("batch/cfw-upgrade/%s" % request_id)

                    if response["status"] == "complete":
                        self.upgrade_in_progress = False
                        break
                    elif response["status"] in ["failed", "cancelled"]:
                        self.module.fail_json(msg="Firmware upgrade failed to complete. Array [%s]." % self.ssid)
                except Exception as error:
                    self.module.fail_json(msg="Failed to retrieve firmware upgrade status. Array [%s]. Error [%s]." % (self.ssid, to_native(error)))
        else:
            for count in range(0, int(self.REBOOT_TIMEOUT_SEC / 5)):
                try:
                    sleep(5)
                    rc_firmware, firmware = self.request("storage-systems/%s/graph/xpath-filter?query=/sa/saData/fwVersion" % self.ssid)
                    rc_nvsram, nvsram = self.request("storage-systems/%s/graph/xpath-filter?query=/sa/saData/nvsramVersion" % self.ssid)

                    if six.b(firmware[0]) == self.firmware_version() and six.b(nvsram[0]) == self.nvsram_version():
                        self.upgrade_in_progress = False
                        break
                except Exception as error:
                    pass
            else:
                self.module.fail_json(msg="Timed out waiting for firmware upgrade to complete. Array [%s]." % self.ssid)

    def proxy_upgrade(self):
        """Activate previously uploaded firmware related files."""
        request_id = None
        if self.is_firmware_bundled():
            data = {"activate": True,
                    "firmwareFile": self.firmware_name,
                    "nvsramFile": self.nvsram_name,
                    "systemInfos": [{"systemId": self.ssid,
                                     "allowNonOptimalActivation": self.ignore_health_check}]}
            try:
                rc, response = self.request("batch/cfw-upgrade", method="POST", data=data)
                request_id = response["requestId"]
            except Exception as error:
                self.module.fail_json(msg="Failed to initiate firmware upgrade. Array [%s]. Error [%s]." % (self.ssid, to_native(error)))

        else:
            data = {"stageFirmware": False,
                    "skipMelCheck": self.ignore_health_check,
                    "cfwFile": self.firmware_name,
                    "nvsramFile": self.nvsram_name}
            try:
                rc, response = self.request("storage-systems/%s/cfw-upgrade" % self.ssid, method="POST", data=data)
                request_id = response["requestId"]
            except Exception as error:
                self.module.fail_json(msg="Failed to initiate firmware upgrade. Array [%s]. Error [%s]." % (self.ssid, to_native(error)))

        self.upgrade_in_progress = True
        if self.wait_for_completion:
            self.proxy_wait_for_upgrade(request_id)

    def apply(self):
        """Upgrade controller firmware."""
        self.check_system_health()

        # Verify firmware compatibility and whether changes are required
        if self.is_embedded():
            self.embedded_check_compatibility()
        else:
            self.proxy_check_upgrade_required()

            # This will upload the firmware files to the web services proxy but not to the controller
            if self.upgrade_required:
                self.proxy_upload_and_check_compatibility()

        # Perform upgrade
        if self.upgrade_required and not self.module.check_mode:
            if self.is_embedded():
                self.embedded_upgrade()
            else:
                self.proxy_upgrade()

        self.module.exit_json(changed=self.upgrade_required, upgrade_in_process=self.upgrade_in_progress, status=self.module_info)


def main():
    firmware = NetAppESeriesFirmware()
    firmware.apply()


if __name__ == '__main__':
    main()
