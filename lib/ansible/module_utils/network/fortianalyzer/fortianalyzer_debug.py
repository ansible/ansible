# This code is part of Ansible, but is an independent component.
# This particular file snippet, and this file snippet only, is BSD licensed.
# Modules you write using this snippet, which is embedded dynamically by Ansible
# still belong to the author of the module, and may assign their own license
# to the complete work.
#
# (c) 2017 Fortinet, Inc
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright notice,
#      this list of conditions and the following disclaimer in the documentation
#      and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import re


# THIS FUNCTION LOGS ALL WEB REQUESTS
def debug_dump(response, datagram, paramgram, url, mode, module_name=None, filepath="/tmp/faz_debug_dump/"):
    '''
    This function will return basic information about the session, and web call made
    and record it to files
    '''

    try:
        import os, json, inspect
    except Exception as e: print(e)

    try:
        myself = inspect.stack()[2][3]
        whole_stack = inspect.stack()
    except:
        return "failed on getting name split"

    # TRY GETTING MODULE NAME FROM STACK
    try:
        module_name = whole_stack[4][1].replace("/tmp/ansible_", "")
        module_name = re.sub(r'_payload.*', '', module_name)
    except Exception as err:
        print err
        pass

    try:
        pyfmg_log_add = {
                        "paramgram_used": paramgram,
                        "datagram_sent": datagram,
                        "raw_response": response[1],
                        "post_method": mode
                        }
    except:
        print "couldn't create log add ..."
        return "FAILED on log add paramgram"

    # CHECK FOR THE URL AND INSERT THAT
    try:
        url = response[1]["url"]
    except:
        url = url
        pyfmg_log_add["url"] = url

    if not os.path.exists(filepath):
        os.makedirs(filepath)
    file_name = "test_" + str(module_name).replace(".py", "") + ".json"
    full_filepath = str(filepath) + str(file_name)
    file_append_text = json.dumps(pyfmg_log_add, indent=3)


    # CHECK FOR EXISTING FILE AND GET ITS JSON CONTENTS IF IT'S THERE
    # IF NOT, CREATE A NEW ONE
    if os.path.isfile(full_filepath):
        with open(full_filepath) as data_file:
            existing_data = json.load(data_file)
        try:
            myself_stanza = existing_data[myself]
        except:
            myself_stanza = None
        if myself_stanza is not None:
            existing_data[myself].append(pyfmg_log_add)
        else:
            existing_data[myself] = list()
            existing_data[myself].append(pyfmg_log_add)
        out_log_file = open(full_filepath, "w")
        file_append_text_output = json.dumps(existing_data, indent=3)
        out_log_file.writelines(file_append_text_output + "\n")
        out_log_file.close()
    else:
        out_log_file = open(full_filepath, "w")
        existing_data = {
            myself: list()
        }
        existing_data[myself].append(pyfmg_log_add)
        new_file_out_text = json.dumps(existing_data, indent=3)
        out_log_file.writelines(str(new_file_out_text))
        out_log_file.close()

    return