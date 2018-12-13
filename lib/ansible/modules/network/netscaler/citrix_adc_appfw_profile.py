#!/usr/bin/python
# -*- coding: utf-8 -*-

#  Copyright (c) 2018 Citrix Systems
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: citrix_adc_appfw_profile
short_description: Manage Citrix ADC Web Application Firewall profiles.
description:
    - Manage Citrix ADC Web Application Firewall profiles.
    - The module uses the NITRO API to make configuration changes to WAF policy labels on the target Citrix ADC.
    - The NITRO API reference can be found at https://developer-docs.citrix.com/projects/netscaler-nitro-api/en/latest
    - Note that due to NITRO API limitations the module may incorrectly report a changed status when no configuration change has taken place.

version_added: "2.8.0"

author:
    - George Nikolopoulos (@giorgos-nikolopoulos)
    - Sumanth Lingappa (@sumanth-lingappa)

options:

    name:
        description:
            - >-
                Name for the profile. Must begin with a letter, number, or the underscore character (_), and must
                only letters, numbers, and the hyphen (-), period (.), pound (#), space ( ), at (@), equals (=),
                (:), and underscore (_) characters. Cannot be changed after the profile is added.
            - ""
            - "The following requirement applies only to the NetScaler CLI:"
            - >-
                If the name includes one or more spaces, enclose the name in double or single quotation marks (for
                "my profile" or 'my profile').
        type: str

    defaults:
        choices:
            - 'basic'
            - 'advanced'
        description:
            - >-
                Default configuration to apply to the profile. Basic defaults are intended for standard content that
                little further configuration, such as static web site content. Advanced defaults are intended for
                content that requires significant specialized configuration, such as heavily scripted or dynamic
            - ""
            - >-
                CLI users: When adding an application firewall profile, you can set either the defaults or the type,
                not both. To set both options, create the profile by using the add appfw profile command, and then
                the set appfw profile command to configure the other option.
        type: str

    starturlaction:
        choices:
            - 'none'
            - 'block'
            - 'learn'
            - 'log'
            - 'stats'
        description:
            - "One or more Start URL actions. Available settings function as follows:"
            - "* Block - Block connections that violate this security check."
            - "* Learn - Use the learning engine to generate a list of exceptions to this security check."
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check."
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -startURLaction" followed by the
                to be enabled. To turn off all actions, type "set appfw profile -startURLaction none".
        type: list

    contenttypeaction:
        choices:
            - 'none'
            - 'block'
            - 'learn'
            - 'log'
            - 'stats'
        description:
            - "One or more Content-type actions. Available settings function as follows:"
            - "* Block - Block connections that violate this security check."
            - "* Learn - Use the learning engine to generate a list of exceptions to this security check."
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check."
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -contentTypeaction" followed by the
                to be enabled. To turn off all actions, type "set appfw profile -contentTypeaction none".
        type: list

    inspectcontenttypes:
        choices:
            - 'none'
            - 'application/x-www-form-urlencoded'
            - 'multipart/form-data'
            - 'text/x-gwt-rpc'
        description:
            - "One or more InspectContentType lists. "
            - "* application/x-www-form-urlencoded"
            - "* multipart/form-data"
            - "* text/x-gwt-rpc"
            - ""
            - >-
                CLI users: To enable, type "set appfw profile -InspectContentTypes" followed by the content types to
                inspected.
        type: list

    starturlclosure:
        description:
            - "Toggle  the state of Start URL Closure."
        type: bool

    denyurlaction:
        choices:
            - 'none'
            - 'block'
            - 'learn'
            - 'log'
            - 'stats'
        description:
            - "One or more Deny URL actions. Available settings function as follows:"
            - "* Block - Block connections that violate this security check."
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check."
            - ""
            - >-
                NOTE: The Deny URL check takes precedence over the Start URL check. If you enable blocking for the
                URL check, the application firewall blocks any URL that is explicitly blocked by a Deny URL, even if
                same URL would otherwise be allowed by the Start URL check.
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -denyURLaction" followed by the
                to be enabled. To turn off all actions, type "set appfw profile -denyURLaction none".
        type: list

    refererheadercheck:
        choices:
            - 'OFF'
            - 'if_present'
            - 'AlwaysExceptStartURLs'
            - 'AlwaysExceptFirstRequest'
        description:
            - "Enable validation of Referer headers. "
            - >-
                Referer validation ensures that a web form that a user sends to your web site originally came from
                web site, not an outside attacker.
            - >-
                Although this parameter is part of the Start URL check, referer validation protects against
                request forgery (CSRF) attacks, not Start URL attacks.
        type: str

    cookieconsistencyaction:
        choices:
            - 'none'
            - 'block'
            - 'learn'
            - 'log'
            - 'stats'
        description:
            - "One or more Cookie Consistency actions. Available settings function as follows:"
            - "* Block - Block connections that violate this security check."
            - "* Learn - Use the learning engine to generate a list of exceptions to this security check."
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check."
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -cookieConsistencyAction" followed
                the actions to be enabled. To turn off all actions, type "set appfw profile -cookieConsistencyAction
        type: list

    cookietransforms:
        description:
            - "Perform the specified type of cookie transformation. "
            - "Available settings function as follows: "
            - "* Encryption - Encrypt cookies."
            - "* Proxying - Mask contents of server cookies by sending proxy cookie to users."
            - >-
                * Cookie flags - Flag cookies as HTTP only to prevent scripts on user's browser from accessing and
                modifying them.
            - >-
                CAUTION: Make sure that this parameter is set to ON if you are configuring any cookie
                If it is set to OFF, no cookie transformations are performed regardless of any other settings.
        type: bool

    cookieencryption:
        choices:
            - 'none'
            - 'decryptOnly'
            - 'encryptSessionOnly'
            - 'encryptAll'
        description:
            - "Type of cookie encryption. Available settings function as follows:"
            - "* None - Do not encrypt cookies."
            - "* Decrypt Only - Decrypt encrypted cookies, but do not encrypt cookies."
            - "* Encrypt Session Only - Encrypt session cookies, but not permanent cookies."
            - "* Encrypt All - Encrypt all cookies."
        type: str

    cookieproxying:
        choices:
            - 'none'
            - 'sessionOnly'
        description:
            - "Cookie proxy setting. Available settings function as follows:"
            - "* None - Do not proxy cookies."
            - >-
                * Session Only - Proxy session cookies by using the NetScaler session ID, but do not proxy permanent
        type: str

    addcookieflags:
        choices:
            - 'none'
            - 'httpOnly'
            - 'secure'
            - 'all'
        description:
            - "Add the specified flags to cookies. Available settings function as follows:"
            - "* None - Do not add flags to cookies."
            - "* HTTP Only - Add the HTTP Only flag to cookies, which prevents scripts from accessing cookies."
            - "* Secure - Add Secure flag to cookies."
            - "* All - Add both HTTPOnly and Secure flags to cookies."
        type: str

    fieldconsistencyaction:
        choices:
            - 'none'
            - 'block'
            - 'learn'
            - 'log'
            - 'stats'
        description:
            - "One or more Form Field Consistency actions. Available settings function as follows:"
            - "* Block - Block connections that violate this security check."
            - "* Learn - Use the learning engine to generate a list of exceptions to this security check."
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check."
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -fieldConsistencyaction" followed
                the actions to be enabled. To turn off all actions, type "set appfw profile -fieldConsistencyAction
        type: list

    csrftagaction:
        choices:
            - 'none'
            - 'block'
            - 'learn'
            - 'log'
            - 'stats'
        description:
            - >-
                One or more Cross-Site Request Forgery (CSRF) Tagging actions. Available settings function as
            - "* Block - Block connections that violate this security check."
            - "* Learn - Use the learning engine to generate a list of exceptions to this security check."
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check."
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -CSRFTagAction" followed by the
                to be enabled. To turn off all actions, type "set appfw profile -CSRFTagAction none".
        type: list

    crosssitescriptingaction:
        choices:
            - 'none'
            - 'block'
            - 'learn'
            - 'log'
            - 'stats'
        description:
            - "One or more Cross-Site Scripting (XSS) actions. Available settings function as follows:"
            - "* Block - Block connections that violate this security check."
            - "* Learn - Use the learning engine to generate a list of exceptions to this security check."
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check."
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -crossSiteScriptingAction" followed
                the actions to be enabled. To turn off all actions, type "set appfw profile -crossSiteScriptingAction
        type: list

    crosssitescriptingtransformunsafehtml:
        description:
            - >-
                Transform cross-site scripts. This setting configures the application firewall to disable dangerous
                instead of blocking the request.
            - >-
                CAUTION: Make sure that this parameter is set to ON if you are configuring any cross-site scripting
                If it is set to OFF, no cross-site scripting transformations are performed regardless of any other
        type: bool

    crosssitescriptingcheckcompleteurls:
        description:
            - "Check complete URLs for cross-site scripts, instead of just the query portions of URLs."
        type: bool

    sqlinjectionaction:
        choices:
            - 'none'
            - 'block'
            - 'learn'
            - 'log'
            - 'stats'
        description:
            - "One or more HTML SQL Injection actions. Available settings function as follows:"
            - "* Block - Block connections that violate this security check."
            - "* Learn - Use the learning engine to generate a list of exceptions to this security check."
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check."
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -SQLInjectionAction" followed by
                actions to be enabled. To turn off all actions, type "set appfw profile -SQLInjectionAction none".
        type: list

    sqlinjectiontransformspecialchars:
        description:
            - >-
                Transform injected SQL code. This setting configures the application firewall to disable SQL special
                instead of blocking the request. Since most SQL servers require a special string to activate an SQL
                in most cases a request that contains injected SQL code is safe if special strings are disabled.
            - >-
                CAUTION: Make sure that this parameter is set to ON if you are configuring any SQL injection
                If it is set to OFF, no SQL injection transformations are performed regardless of any other settings.
        type: bool

    sqlinjectiononlycheckfieldswithsqlchars:
        description:
            - "Check only form fields that contain SQL special strings (characters) for injected SQL code."
            - >-
                Most SQL servers require a special string to activate an SQL request, so SQL code without a special
                is harmless to most SQL servers.
        type: bool

    sqlinjectiontype:
        choices:
            - 'SQLSplChar'
            - 'SQLKeyword'
            - 'SQLSplCharORKeyword'
            - 'SQLSplCharANDKeyword'
        description:
            - "Available SQL injection types. "
            - "-SQLSplChar              : Checks for SQL Special Chars"
            - "-SQLKeyword		 : Checks for SQL Keywords"
            - "-SQLSplCharANDKeyword    : Checks for both and blocks if both are found"
            - "-SQLSplCharORKeyword     : Checks for both and blocks if anyone is found"
        type: str

    sqlinjectionchecksqlwildchars:
        description:
            - "Check for form fields that contain SQL wild chars ."
        type: bool

    fieldformataction:
        choices:
            - 'none'
            - 'block'
            - 'learn'
            - 'log'
            - 'stats'
        description:
            - "One or more Field Format actions. Available settings function as follows:"
            - "* Block - Block connections that violate this security check."
            - >-
                * Learn - Use the learning engine to generate a list of suggested web form fields and field format
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check."
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -fieldFormatAction" followed by the
                to be enabled. To turn off all actions, type "set appfw profile -fieldFormatAction none".
        type: list

    defaultfieldformattype:
        description:
            - >-
                Designate a default field type to be applied to web form fields that do not have a field type
                assigned to them.
        type: str

    defaultfieldformatminlength:
        description:
            - >-
                Minimum length, in characters, for data entered into a field that is assigned the default field type.
            - >-
                To disable the minimum and maximum length settings and allow data of any length to be entered into
                field, set this parameter to zero (0).
        type: str

    defaultfieldformatmaxlength:
        description:
            - >-
                Maximum length, in characters, for data entered into a field that is assigned the default field type.
        type: str

    bufferoverflowaction:
        choices:
            - 'none'
            - 'block'
            - 'learn'
            - 'log'
            - 'stats'
        description:
            - "One or more Buffer Overflow actions. Available settings function as follows:"
            - "* Block - Block connections that violate this security check."
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check."
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -bufferOverflowAction" followed by
                actions to be enabled. To turn off all actions, type "set appfw profile -bufferOverflowAction none".
        type: list

    bufferoverflowmaxurllength:
        description:
            - >-
                Maximum length, in characters, for URLs on your protected web sites. Requests with longer URLs are
        type: str

    bufferoverflowmaxheaderlength:
        description:
            - >-
                Maximum length, in characters, for HTTP headers in requests sent to your protected web sites.
                with longer headers are blocked.
        type: str

    bufferoverflowmaxcookielength:
        description:
            - >-
                Maximum length, in characters, for cookies sent to your protected web sites. Requests with longer
                are blocked.
        type: str

    creditcardaction:
        choices:
            - 'none'
            - 'block'
            - 'learn'
            - 'log'
            - 'stats'
        description:
            - "One or more Credit Card actions. Available settings function as follows:"
            - "* Block - Block connections that violate this security check."
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check."
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -creditCardAction" followed by the
                to be enabled. To turn off all actions, type "set appfw profile -creditCardAction none".
        type: list

    creditcard:
        choices:
            - 'none'
            - 'visa'
            - 'mastercard'
            - 'discover'
            - 'amex'
            - 'jcb'
            - 'dinersclub'
        description:
            - "Credit card types that the application firewall should protect."
        type: list

    creditcardmaxallowed:
        description:
            - >-
                This parameter value is used by the block action. It represents the maximum number of credit card
                that can appear on a web page served by your protected web sites. Pages that contain more credit card
                are blocked.
        type: str

    creditcardxout:
        description:
            - >-
                Mask any credit card number detected in a response by replacing each digit, except the digits in the
                group, with the letter "X."
        type: bool

    dosecurecreditcardlogging:
        description:
            - "Setting this option logs credit card numbers in the response when the match is found."
        type: bool

    streaming:
        description:
            - >-
                Setting this option converts content-length form submission requests (requests with content-type
                or "multipart/form-data") to chunked requests when atleast one of the following protections : SQL
                protection, XSS protection, form field consistency protection, starturl closure, CSRF tagging is
                Please make sure that the backend server accepts chunked requests before enabling this option.
        type: bool

    trace:
        description:
            - "Toggle  the state of trace"
        type: bool

    requestcontenttype:
        description:
            - "Default Content-Type header for requests. "
            - >-
                A Content-Type header can contain 0-255 letters, numbers, and the hyphen (-) and underscore (_)
        type: str

    responsecontenttype:
        description:
            - "Default Content-Type header for responses. "
            - >-
                A Content-Type header can contain 0-255 letters, numbers, and the hyphen (-) and underscore (_)
        type: str

    xmldosaction:
        choices:
            - 'none'
            - 'block'
            - 'learn'
            - 'log'
            - 'stats'
        description:
            - "One or more XML Denial-of-Service (XDoS) actions. Available settings function as follows:"
            - "* Block - Block connections that violate this security check."
            - "* Learn - Use the learning engine to generate a list of exceptions to this security check."
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check."
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -XMLDoSAction" followed by the
                to be enabled. To turn off all actions, type "set appfw profile -XMLDoSAction none".
        type: list

    xmlformataction:
        choices:
            - 'none'
            - 'block'
            - 'learn'
            - 'log'
            - 'stats'
        description:
            - "One or more XML Format actions. Available settings function as follows:"
            - "* Block - Block connections that violate this security check."
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check."
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -XMLFormatAction" followed by the
                to be enabled. To turn off all actions, type "set appfw profile -XMLFormatAction none".
        type: list

    xmlsqlinjectionaction:
        choices:
            - 'none'
            - 'block'
            - 'learn'
            - 'log'
            - 'stats'
        description:
            - "One or more XML SQL Injection actions. Available settings function as follows:"
            - "* Block - Block connections that violate this security check."
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check."
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -XMLSQLInjectionAction" followed by
                actions to be enabled. To turn off all actions, type "set appfw profile -XMLSQLInjectionAction none".
        type: list

    xmlsqlinjectiononlycheckfieldswithsqlchars:
        description:
            - >-
                Check only form fields that contain SQL special characters, which most SQL servers require before
                an SQL command, for injected SQL.
        type: bool

    xmlsqlinjectiontype:
        choices:
            - 'SQLSplChar'
            - 'SQLKeyword'
            - 'SQLSplCharORKeyword'
            - 'SQLSplCharANDKeyword'
        description:
            - "Available SQL injection types."
            - "-SQLSplChar              : Checks for SQL Special Chars"
            - "-SQLKeyword              : Checks for SQL Keywords"
            - "-SQLSplCharANDKeyword    : Checks for both and blocks if both are found"
            - "-SQLSplCharORKeyword     : Checks for both and blocks if anyone is found"
        type: str

    xmlsqlinjectionchecksqlwildchars:
        description:
            - "Check for form fields that contain SQL wild chars ."
        type: bool

    xmlsqlinjectionparsecomments:
        choices:
            - 'checkall'
            - 'ansi'
            - 'nested'
            - 'ansinested'
        description:
            - >-
                Parse comments in XML Data and exempt those sections of the request that are from the XML SQL
                check. You must configure the type of comments that the application firewall is to detect and exempt
                this security check. Available settings function as follows:
            - "* Check all - Check all content."
            - "* ANSI - Exempt content that is part of an ANSI (Mozilla-style) comment. "
            - "* Nested - Exempt content that is part of a nested (Microsoft-style) comment."
            - "* ANSI Nested - Exempt content that is part of any type of comment."
        type: str

    xmlxssaction:
        choices:
            - 'none'
            - 'block'
            - 'learn'
            - 'log'
            - 'stats'
        description:
            - "One or more XML Cross-Site Scripting actions. Available settings function as follows:"
            - "* Block - Block connections that violate this security check."
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check."
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -XMLXSSAction" followed by the
                to be enabled. To turn off all actions, type "set appfw profile -XMLXSSAction none".
        type: list

    xmlwsiaction:
        choices:
            - 'none'
            - 'block'
            - 'learn'
            - 'log'
            - 'stats'
        description:
            - "One or more Web Services Interoperability (WSI) actions. Available settings function as follows:"
            - "* Block - Block connections that violate this security check."
            - "* Learn - Use the learning engine to generate a list of exceptions to this security check."
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check."
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -XMLWSIAction" followed by the
                to be enabled. To turn off all actions, type "set appfw profile -XMLWSIAction none".
        type: list

    xmlattachmentaction:
        choices:
            - 'none'
            - 'block'
            - 'learn'
            - 'log'
            - 'stats'
        description:
            - "One or more XML Attachment actions. Available settings function as follows:"
            - "* Block - Block connections that violate this security check."
            - "* Learn - Use the learning engine to generate a list of exceptions to this security check."
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check."
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -XMLAttachmentAction" followed by
                actions to be enabled. To turn off all actions, type "set appfw profile -XMLAttachmentAction none".
        type: list

    xmlvalidationaction:
        choices:
            - 'none'
            - 'block'
            - 'learn'
            - 'log'
            - 'stats'
        description:
            - "One or more XML Validation actions. Available settings function as follows:"
            - "* Block - Block connections that violate this security check."
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check. "
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -XMLValidationAction" followed by
                actions to be enabled. To turn off all actions, type "set appfw profile -XMLValidationAction none".
        type: list

    xmlerrorobject:
        description:
            - >-
                Name to assign to the XML Error Object, which the application firewall displays when a user request
                blocked.
            - >-
                Must begin with a letter, number, or the underscore character (_), and must contain only letters,
                and the hyphen (-), period (.) pound (#), space ( ), at (@), equals (=), colon (:), and underscore
                Cannot be changed after the XML error object is added.
            - ""
            - "The following requirement applies only to the NetScaler CLI:"
            - >-
                If the name includes one or more spaces, enclose the name in double or single quotation marks (for
                "my XML error object" or 'my XML error object').
        type: str

    customsettings:
        description:
            - "Object name for custom settings."
            - "This check is applicable to Profile Type: HTML, XML. "
        type: str

    signatures:
        description:
            - "Object name for signatures."
            - "This check is applicable to Profile Type: HTML, XML. "
        type: str

    xmlsoapfaultaction:
        choices:
            - 'none'
            - 'block'
            - 'log'
            - 'remove'
            - 'stats'
        description:
            - "One or more XML SOAP Fault Filtering actions. Available settings function as follows:"
            - "* Block - Block connections that violate this security check."
            - "* Log - Log violations of this security check."
            - "* Stats - Generate statistics for this security check."
            - "* None - Disable all actions for this security check."
            - "* Remove - Remove all violations for this security check."
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -XMLSOAPFaultAction" followed by
                actions to be enabled. To turn off all actions, type "set appfw profile -XMLSOAPFaultAction none".
        type: list

    usehtmlerrorobject:
        description:
            - >-
                Send an imported HTML Error object to a user when a request is blocked, instead of redirecting the
                to the designated Error URL.
        type: bool

    errorurl:
        description:
            - "URL that application firewall uses as the Error URL."
        type: str

    htmlerrorobject:
        description:
            - "Name to assign to the HTML Error Object. "
            - >-
                Must begin with a letter, number, or the underscore character (_), and must contain only letters,
                and the hyphen (-), period (.) pound (#), space ( ), at (@), equals (=), colon (:), and underscore
                Cannot be changed after the HTML error object is added.
            - ""
            - "The following requirement applies only to the NetScaler CLI:"
            - >-
                If the name includes one or more spaces, enclose the name in double or single quotation marks (for
                "my HTML error object" or 'my HTML error object').
        type: str

    logeverypolicyhit:
        description:
            - "Log every profile match, regardless of security checks results."
        type: bool

    stripcomments:
        description:
            - "Strip HTML comments."
            - "This check is applicable to Profile Type: HTML. "
        type: bool

    striphtmlcomments:
        choices:
            - 'none'
            - 'all'
            - 'exclude_script_tag'
        description:
            - >-
                Strip HTML comments before forwarding a web page sent by a protected web site in response to a user
        type: str

    stripxmlcomments:
        choices:
            - 'none'
            - 'all'
        description:
            - >-
                Strip XML comments before forwarding a web page sent by a protected web site in response to a user
        type: str

    exemptclosureurlsfromsecuritychecks:
        description:
            - >-
                Exempt URLs that pass the Start URL closure check from SQL injection, cross-site script, field format
                field consistency security checks at locations other than headers.
        type: bool

    defaultcharset:
        description:
            - >-
                Default character set for protected web pages. Web pages sent by your protected web sites in response
                user requests are assigned this character set if the page does not already specify a character set.
                character sets supported by the application firewall are:
            - "* iso-8859-1 (English US)"
            - "* big5 (Chinese Traditional)"
            - "* gb2312 (Chinese Simplified)"
            - "* sjis (Japanese Shift-JIS)"
            - "* euc-jp (Japanese EUC-JP)"
            - "* iso-8859-9 (Turkish)"
            - "* utf-8 (Unicode)"
            - "* euc-kr (Korean)"
        type: str

    postbodylimit:
        description:
            - "Maximum allowed HTTP post body size, in bytes."
        type: str

    fileuploadmaxnum:
        description:
            - >-
                Maximum allowed number of file uploads per form-submission request. The maximum setting (65535)
                an unlimited number of uploads.
        type: str

    canonicalizehtmlresponse:
        description:
            - >-
                Perform HTML entity encoding for any special characters in responses sent by your protected web
        type: bool

    enableformtagging:
        description:
            - >-
                Enable tagging of web form fields for use by the Form Field Consistency and CSRF Form Tagging checks.
        type: bool

    sessionlessfieldconsistency:
        choices:
            - 'OFF'
            - 'ON'
            - 'postOnly'
        description:
            - "Perform sessionless Field Consistency Checks."
        type: str

    sessionlessurlclosure:
        description:
            - "Enable session less URL Closure Checks."
            - "This check is applicable to Profile Type: HTML. "
        type: bool

    semicolonfieldseparator:
        description:
            - "Allow ';' as a form field separator in URL queries and POST form bodies. "
        type: bool

    excludefileuploadfromchecks:
        description:
            - "Exclude uploaded files from Form checks."
        type: bool

    sqlinjectionparsecomments:
        choices:
            - 'checkall'
            - 'ansi'
            - 'nested'
            - 'ansinested'
        description:
            - >-
                Parse HTML comments and exempt them from the HTML SQL Injection check. You must specify the type of
                that the application firewall is to detect and exempt from this security check. Available settings
                as follows:
            - "* Check all - Check all content."
            - "* ANSI - Exempt content that is part of an ANSI (Mozilla-style) comment. "
            - "* Nested - Exempt content that is part of a nested (Microsoft-style) comment."
            - "* ANSI Nested - Exempt content that is part of any type of comment."
        type: str

    invalidpercenthandling:
        choices:
            - 'apache_mode'
            - 'asp_mode'
            - 'secure_mode'
        description:
            - >-
                Configure the method that the application firewall uses to handle percent-encoded names and values.
                settings function as follows:
            - "* apache_mode - Apache format."
            - "* asp_mode - Microsoft ASP format."
            - "* secure_mode - Secure format."
        type: str

    type:
        choices:
            - 'HTML'
            - 'XML'
        description:
            - >-
                Application firewall profile type, which controls which security checks and settings are applied to
                that is filtered with the profile. Available settings function as follows:
            - "* HTML - HTML-based web sites."
            - "* XML - XML-based web sites and services."
            - >-
                * HTML XML (Web 2.0) - Sites that contain both HTML and XML content, such as ATOM feeds, blogs, and
                feeds.
        type: list

    checkrequestheaders:
        description:
            - "Check request headers as well as web forms for injected SQL and cross-site scripts."
        type: bool

    optimizepartialreqs:
        description:
            - "Optimize handle of HTTP partial requests i.e. those with range headers."
            - "Available settings are as follows: "
            - >-
                * ON - Partial requests by the client result in partial requests to the backend server in most cases.
            - "* OFF - Partial requests by the client are changed to full requests to the backend server"
        type: bool

    urldecoderequestcookies:
        description:
            - "URL Decode request cookies before subjecting them to SQL and cross-site scripting checks."
        type: bool

    comment:
        description:
            - "Any comments about the purpose of profile, or other useful information about the profile."
        type: str

    percentdecoderecursively:
        description:
            - "Configure whether the application firewall should use percentage recursive decoding"
        type: bool

    multipleheaderaction:
        choices:
            - 'block'
            - 'keepLast'
            - 'log'
            - 'none'
        description:
            - "One or more multiple header actions. Available settings function as follows:"
            - "* Block - Block connections that have multiple headers."
            - "* Log - Log connections that have multiple headers."
            - "* KeepLast - Keep only last header when multiple headers are present."
            - ""
            - >-
                CLI users: To enable one or more actions, type "set appfw profile -multipleHeaderAction" followed by
                actions to be enabled.
        type: list

    archivename:
        description:
            - "Source for tar archive."
        type: str




    contenttype_bindings:
        description: contenttype bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - contenttype
                    - state
                    - comment


    cookieconsistency_bindings:
        description: cookieconsistency bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - cookieconsistency
                    - isregex
                    - state
                    - comment


    creditcardnumber_bindings:
        description: creditcardnumber bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - creditcardnumber
                    - creditcardnumberurl
                    - state
                    - comment


    crosssitescripting_bindings:
        description: crosssitescripting bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - crosssitescripting
                    - isregex_xss
                    - formactionurl_xss
                    - as_scan_location_xss
                    - as_value_type_xss
                    - as_value_expr_xss
                    - isvalueregex_xss
                    - state
                    - comment


    csrftag_bindings:
        description: csrftag bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - csrftag
                    - csrfformactionurl
                    - state
                    - comment


    denyurl_bindings:
        description: denyurl bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - denyurl
                    - state
                    - comment


    excluderescontenttype_bindings:
        description: excluderescontenttype bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - excluderescontenttype
                    - state
                    - comment


    fieldconsistency_bindings:
        description: fieldconsistency bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - fieldconsistency
                    - isregex_ffc
                    - formactionurl_ffc
                    - state
                    - comment


    fieldformat_bindings:
        description: fieldformat bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - fieldformat
                    - isregex_ff
                    - formactionurl_ff
                    - fieldtype
                    - fieldformatminlength
                    - fieldformatmaxlength
                    - state
                    - comment


    safeobject_bindings:
        description: safeobject bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - safeobject
                    - as_expression
                    - maxmatchlength
                    - action
                    - state
                    - comment


    sqlinjection_bindings:
        description: sqlinjection bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - sqlinjection
                    - isregex_sql
                    - formactionurl_sql
                    - as_scan_location_sql
                    - as_value_type_sql
                    - as_value_expr_sql
                    - isvalueregex_sql
                    - state
                    - comment


    starturl_bindings:
        description: starturl bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - starturl
                    - state
                    - comment


    trustedlearningclients_bindings:
        description: trustedlearningclients bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - trustedlearningclients
                    - state
                    - comment


    xmlattachmenturl_bindings:
        description: xmlattachmenturl bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - xmlattachmenturl
                    - xmlmaxattachmentsizecheck
                    - xmlmaxattachmentsize
                    - xmlattachmentcontenttypecheck
                    - xmlattachmentcontenttype
                    - state
                    - comment


    xmldosurl_bindings:
        description: xmldosurl bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - xmldosurl
                    - xmlmaxelementdepthcheck
                    - xmlmaxelementdepth
                    - xmlmaxelementnamelengthcheck
                    - xmlmaxelementnamelength
                    - xmlmaxelementscheck
                    - xmlmaxelements
                    - xmlmaxelementchildrencheck
                    - xmlmaxelementchildren
                    - xmlmaxnodescheck
                    - xmlmaxnodes
                    - xmlmaxentityexpansionscheck
                    - xmlmaxentityexpansions
                    - xmlmaxentityexpansiondepthcheck
                    - xmlmaxentityexpansiondepth
                    - xmlmaxattributescheck
                    - xmlmaxattributes
                    - xmlmaxattributenamelengthcheck
                    - xmlmaxattributenamelength
                    - xmlmaxattributevaluelengthcheck
                    - xmlmaxattributevaluelength
                    - xmlmaxnamespacescheck
                    - xmlmaxnamespaces
                    - xmlmaxnamespaceurilengthcheck
                    - xmlmaxnamespaceurilength
                    - xmlmaxchardatalengthcheck
                    - xmlmaxchardatalength
                    - xmlmaxfilesizecheck
                    - xmlmaxfilesize
                    - xmlminfilesizecheck
                    - xmlminfilesize
                    - xmlblockpi
                    - xmlblockdtd
                    - xmlblockexternalentities
                    - xmlsoaparraycheck
                    - xmlmaxsoaparraysize
                    - xmlmaxsoaparrayrank
                    - state
                    - comment


    xmlsqlinjection_bindings:
        description: xmlsqlinjection bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - xmlsqlinjection
                    - isregex_xmlsql
                    - as_scan_location_xmlsql
                    - state
                    - comment


    xmlvalidationurl_bindings:
        description: xmlvalidationurl bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - xmlvalidationurl
                    - xmlvalidateresponse
                    - xmlwsdl
                    - xmladditionalsoapheaders
                    - xmlendpointcheck
                    - xmlrequestschema
                    - xmlresponseschema
                    - xmlvalidatesoapenvelope
                    - state
                    - comment


    xmlwsiurl_bindings:
        description: xmlwsiurl bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - xmlwsiurl
                    - xmlwsichecks
                    - state
                    - comment


    xmlxss_bindings:
        description: xmlxss bindings
        suboptions:
            mode:
                description:
                    - If mode is C(exact):
                    - Any bindings existing in the target Citrix ADC that are not defined in the attributes list will be removed.
                    - Any bindings not existing in the target Citrix ADC that are defined in the attributes list will be created.
                    - >-
                        Any existing bindings that are defined in the attributes list but have differing attribute values will first
                        be deleted and then recreated with the defined attribute values.
                    - If mode is C(bind):
                    - Any bindings in the attributes list that do not exist will be created on the target Citrix ADC.
                    - >-
                        Any bindings defined in the attributes list that exist on the target Citrix ADC but have different attribute values
                        will first be deleted and then recreated with the defined attribute values.
                    - Existing bindings that are not on the attributes list remain unaffected.
                    - If mode is C(unbind):
                    - Any bindings defined in the attributes list that also exist on the target Citrix ADC will be removed.
                    - Existing bindings that are not on the attributes list remain unaffected.
                choices:
                    - exact
                    - bind
                    - unbind
            attributes:
                description:
                    - List of the attributes dictionaries for the bindings.
                    - Valid attribute keys:
                    - xmlxss
                    - isregex_xmlxss
                    - as_scan_location_xmlxss
                    - state
                    - comment



extends_documentation_fragment: netscaler
'''

EXAMPLES = '''
- name: setup profile with basic presets
  delegate_to: localhost
  citrix_adc_appfw_profile:
    nitro_user: nsroot
    nitro_pass: nsroot
    nsip: 192.168.1.1
    state: present
    name: profile_basic_1
    defaults: basic

- name: setup profile with denyurl bindings
  delegate_to: localhost
  citrix_adc_appfw_profile:
    nitro_user: ''
    nitro_pass: ''
    nsip: ''
    state: present
    name: profile_basic_2
    denyurl_bindings:
      mode: exact
      attributes:
        - state: enabled
          denyurl: denyme.*
          comment: 'denyurl comment'

- name: remove profile
  delegate_to: localhost
  citrix_adc_appfw_profile:
    nitro_user: nsroot
    nitro_pass: nsroot
    nsip: 192.168.1.1
    state: absent
    name: profile_basic_integration_test
    defaults: basic
'''

RETURN = '''
loglines:
    description: list of logged messages by the module
    returned: always
    type: list
    sample: ['message 1', 'message 2']

msg:
    description: Message detailing the failure reason
    returned: failure
    type: str
    sample: "Action does not exist"
'''

import copy
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netscaler.netscaler import NitroResourceConfig, NitroException, netscaler_common_arguments, log, loglines


class ModuleExecutor(object):

    def __init__(self, module):
        self.module = module
        self.main_nitro_class = 'appfwprofile'

        # Dictionary containing attribute information
        # for each NITRO object utilized by this module
        self.attribute_config = {
            'appfwprofile': {
                'attributes_list': [
                    'name',
                    'defaults',
                    'starturlaction',
                    'contenttypeaction',
                    'inspectcontenttypes',
                    'starturlclosure',
                    'denyurlaction',
                    'refererheadercheck',
                    'cookieconsistencyaction',
                    'cookietransforms',
                    'cookieencryption',
                    'cookieproxying',
                    'addcookieflags',
                    'fieldconsistencyaction',
                    'csrftagaction',
                    'crosssitescriptingaction',
                    'crosssitescriptingtransformunsafehtml',
                    'crosssitescriptingcheckcompleteurls',
                    'sqlinjectionaction',
                    'sqlinjectiontransformspecialchars',
                    'sqlinjectiononlycheckfieldswithsqlchars',
                    'sqlinjectiontype',
                    'sqlinjectionchecksqlwildchars',
                    'fieldformataction',
                    'defaultfieldformattype',
                    'defaultfieldformatminlength',
                    'defaultfieldformatmaxlength',
                    'bufferoverflowaction',
                    'bufferoverflowmaxurllength',
                    'bufferoverflowmaxheaderlength',
                    'bufferoverflowmaxcookielength',
                    'creditcardaction',
                    'creditcard',
                    'creditcardmaxallowed',
                    'creditcardxout',
                    'dosecurecreditcardlogging',
                    'streaming',
                    'trace',
                    'requestcontenttype',
                    'responsecontenttype',
                    'xmldosaction',
                    'xmlformataction',
                    'xmlsqlinjectionaction',
                    'xmlsqlinjectiononlycheckfieldswithsqlchars',
                    'xmlsqlinjectiontype',
                    'xmlsqlinjectionchecksqlwildchars',
                    'xmlsqlinjectionparsecomments',
                    'xmlxssaction',
                    'xmlwsiaction',
                    'xmlattachmentaction',
                    'xmlvalidationaction',
                    'xmlerrorobject',
                    'customsettings',
                    'signatures',
                    'xmlsoapfaultaction',
                    'usehtmlerrorobject',
                    'errorurl',
                    'htmlerrorobject',
                    'logeverypolicyhit',
                    'stripcomments',
                    'striphtmlcomments',
                    'stripxmlcomments',
                    'exemptclosureurlsfromsecuritychecks',
                    'defaultcharset',
                    'postbodylimit',
                    'fileuploadmaxnum',
                    'canonicalizehtmlresponse',
                    'enableformtagging',
                    'sessionlessfieldconsistency',
                    'sessionlessurlclosure',
                    'semicolonfieldseparator',
                    'excludefileuploadfromchecks',
                    'sqlinjectionparsecomments',
                    'invalidpercenthandling',
                    'type',
                    'checkrequestheaders',
                    'optimizepartialreqs',
                    'urldecoderequestcookies',
                    'comment',
                    'percentdecoderecursively',
                    'multipleheaderaction',
                    'archivename',
                ],
                'transforms': {
                    'starturlclosure': lambda v: 'ON' if v else 'OFF',
                    'cookietransforms': lambda v: 'ON' if v else 'OFF',
                    'crosssitescriptingtransformunsafehtml': lambda v: 'ON' if v else 'OFF',
                    'crosssitescriptingcheckcompleteurls': lambda v: 'ON' if v else 'OFF',
                    'sqlinjectiontransformspecialchars': lambda v: 'ON' if v else 'OFF',
                    'sqlinjectiononlycheckfieldswithsqlchars': lambda v: 'ON' if v else 'OFF',
                    'sqlinjectionchecksqlwildchars': lambda v: 'ON' if v else 'OFF',
                    'creditcardxout': lambda v: 'ON' if v else 'OFF',
                    'dosecurecreditcardlogging': lambda v: 'ON' if v else 'OFF',
                    'streaming': lambda v: 'ON' if v else 'OFF',
                    'trace': lambda v: 'ON' if v else 'OFF',
                    'xmlsqlinjectiononlycheckfieldswithsqlchars': lambda v: 'ON' if v else 'OFF',
                    'xmlsqlinjectionchecksqlwildchars': lambda v: 'ON' if v else 'OFF',
                    'usehtmlerrorobject': lambda v: 'ON' if v else 'OFF',
                    'logeverypolicyhit': lambda v: 'ON' if v else 'OFF',
                    'stripcomments': lambda v: 'ON' if v else 'OFF',
                    'exemptclosureurlsfromsecuritychecks': lambda v: 'ON' if v else 'OFF',
                    'canonicalizehtmlresponse': lambda v: 'ON' if v else 'OFF',
                    'enableformtagging': lambda v: 'ON' if v else 'OFF',
                    'sessionlessurlclosure': lambda v: 'ON' if v else 'OFF',
                    'semicolonfieldseparator': lambda v: 'ON' if v else 'OFF',
                    'excludefileuploadfromchecks': lambda v: 'ON' if v else 'OFF',
                    'checkrequestheaders': lambda v: 'ON' if v else 'OFF',
                    'optimizepartialreqs': lambda v: 'ON' if v else 'OFF',
                    'urldecoderequestcookies': lambda v: 'ON' if v else 'OFF',
                    'percentdecoderecursively': lambda v: 'ON' if v else 'OFF',
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'name',
                ],
            },
            'contenttype_bindings': {
                'attributes_list': [
                    'contenttype',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'contenttype',
                    'name',
                ],
            },
            'cookieconsistency_bindings': {
                'attributes_list': [
                    'cookieconsistency',
                    'isregex',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'cookieconsistency',
                    'name',
                ],
            },
            'creditcardnumber_bindings': {
                'attributes_list': [
                    'creditcardnumber',
                    'creditcardnumberurl',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'creditcardnumber',
                    'creditcardnumberurl',
                    'name',
                ],
            },
            'crosssitescripting_bindings': {
                'attributes_list': [
                    'crosssitescripting',
                    'isregex_xss',
                    'formactionurl_xss',
                    'as_scan_location_xss',
                    'as_value_type_xss',
                    'as_value_expr_xss',
                    'isvalueregex_xss',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'crosssitescripting',
                    'formactionurl_xss',
                    'as_scan_location_xss',
                    'as_value_type_xss',
                    'as_value_expr_xss',
                    'name',
                ],
            },
            'csrftag_bindings': {
                'attributes_list': [
                    'csrftag',
                    'csrfformactionurl',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'csrftag',
                    'csrfformactionurl',
                    'name',
                ],
            },
            'denyurl_bindings': {
                'attributes_list': [
                    'denyurl',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'denyurl',
                    'name',
                ],
            },
            'excluderescontenttype_bindings': {
                'attributes_list': [
                    'excluderescontenttype',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'excluderescontenttype',
                    'name',
                ],
            },
            'fieldconsistency_bindings': {
                'attributes_list': [
                    'fieldconsistency',
                    'isregex_ffc',
                    'formactionurl_ffc',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'fieldconsistency',
                    'formactionurl_ffc',
                    'name',
                ],
            },
            'fieldformat_bindings': {
                'attributes_list': [
                    'fieldformat',
                    'isregex_ff',
                    'formactionurl_ff',
                    'fieldtype',
                    'fieldformatminlength',
                    'fieldformatmaxlength',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'fieldformat',
                    'formactionurl_ff',
                    'name',
                ],
            },
            'safeobject_bindings': {
                'attributes_list': [
                    'safeobject',
                    'as_expression',
                    'maxmatchlength',
                    'action',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'safeobject',
                    'name',
                ],
            },
            'sqlinjection_bindings': {
                'attributes_list': [
                    'sqlinjection',
                    'isregex_sql',
                    'formactionurl_sql',
                    'as_scan_location_sql',
                    'as_value_type_sql',
                    'as_value_expr_sql',
                    'isvalueregex_sql',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'sqlinjection',
                    'formactionurl_sql',
                    'as_scan_location_sql',
                    'as_value_type_sql',
                    'as_value_expr_sql',
                    'name',
                ],
            },
            'starturl_bindings': {
                'attributes_list': [
                    'starturl',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'starturl',
                    'name',
                ],
            },
            'trustedlearningclients_bindings': {
                'attributes_list': [
                    'trustedlearningclients',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'trustedlearningclients',
                    'name',
                ],
            },
            'xmlattachmenturl_bindings': {
                'attributes_list': [
                    'xmlattachmenturl',
                    'xmlmaxattachmentsizecheck',
                    'xmlmaxattachmentsize',
                    'xmlattachmentcontenttypecheck',
                    'xmlattachmentcontenttype',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'xmlmaxattachmentsizecheck': lambda v: 'ON' if v else 'OFF',
                    'xmlattachmentcontenttypecheck': lambda v: 'ON' if v else 'OFF',
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'xmlattachmenturl',
                    'name',
                ],
            },
            'xmldosurl_bindings': {
                'attributes_list': [
                    'xmldosurl',
                    'xmlmaxelementdepthcheck',
                    'xmlmaxelementdepth',
                    'xmlmaxelementnamelengthcheck',
                    'xmlmaxelementnamelength',
                    'xmlmaxelementscheck',
                    'xmlmaxelements',
                    'xmlmaxelementchildrencheck',
                    'xmlmaxelementchildren',
                    'xmlmaxnodescheck',
                    'xmlmaxnodes',
                    'xmlmaxentityexpansionscheck',
                    'xmlmaxentityexpansions',
                    'xmlmaxentityexpansiondepthcheck',
                    'xmlmaxentityexpansiondepth',
                    'xmlmaxattributescheck',
                    'xmlmaxattributes',
                    'xmlmaxattributenamelengthcheck',
                    'xmlmaxattributenamelength',
                    'xmlmaxattributevaluelengthcheck',
                    'xmlmaxattributevaluelength',
                    'xmlmaxnamespacescheck',
                    'xmlmaxnamespaces',
                    'xmlmaxnamespaceurilengthcheck',
                    'xmlmaxnamespaceurilength',
                    'xmlmaxchardatalengthcheck',
                    'xmlmaxchardatalength',
                    'xmlmaxfilesizecheck',
                    'xmlmaxfilesize',
                    'xmlminfilesizecheck',
                    'xmlminfilesize',
                    'xmlblockpi',
                    'xmlblockdtd',
                    'xmlblockexternalentities',
                    'xmlsoaparraycheck',
                    'xmlmaxsoaparraysize',
                    'xmlmaxsoaparrayrank',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'xmlmaxelementdepthcheck': lambda v: 'ON' if v else 'OFF',
                    'xmlmaxelementnamelengthcheck': lambda v: 'ON' if v else 'OFF',
                    'xmlmaxelementscheck': lambda v: 'ON' if v else 'OFF',
                    'xmlmaxelementchildrencheck': lambda v: 'ON' if v else 'OFF',
                    'xmlmaxnodescheck': lambda v: 'ON' if v else 'OFF',
                    'xmlmaxentityexpansionscheck': lambda v: 'ON' if v else 'OFF',
                    'xmlmaxentityexpansiondepthcheck': lambda v: 'ON' if v else 'OFF',
                    'xmlmaxattributescheck': lambda v: 'ON' if v else 'OFF',
                    'xmlmaxattributenamelengthcheck': lambda v: 'ON' if v else 'OFF',
                    'xmlmaxattributevaluelengthcheck': lambda v: 'ON' if v else 'OFF',
                    'xmlmaxnamespacescheck': lambda v: 'ON' if v else 'OFF',
                    'xmlmaxnamespaceurilengthcheck': lambda v: 'ON' if v else 'OFF',
                    'xmlmaxchardatalengthcheck': lambda v: 'ON' if v else 'OFF',
                    'xmlmaxfilesizecheck': lambda v: 'ON' if v else 'OFF',
                    'xmlminfilesizecheck': lambda v: 'ON' if v else 'OFF',
                    'xmlblockpi': lambda v: 'ON' if v else 'OFF',
                    'xmlblockdtd': lambda v: 'ON' if v else 'OFF',
                    'xmlblockexternalentities': lambda v: 'ON' if v else 'OFF',
                    'xmlsoaparraycheck': lambda v: 'ON' if v else 'OFF',
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'xmldosurl',
                    'name',
                ],
            },
            'xmlsqlinjection_bindings': {
                'attributes_list': [
                    'xmlsqlinjection',
                    'isregex_xmlsql',
                    'as_scan_location_xmlsql',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'xmlsqlinjection',
                    'as_scan_location_xmlsql',
                    'name',
                ],
            },
            'xmlvalidationurl_bindings': {
                'attributes_list': [
                    'xmlvalidationurl',
                    'xmlvalidateresponse',
                    'xmlwsdl',
                    'xmladditionalsoapheaders',
                    'xmlendpointcheck',
                    'xmlrequestschema',
                    'xmlresponseschema',
                    'xmlvalidatesoapenvelope',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'xmlvalidateresponse': lambda v: 'ON' if v else 'OFF',
                    'xmladditionalsoapheaders': lambda v: 'ON' if v else 'OFF',
                    'xmlvalidatesoapenvelope': lambda v: 'ON' if v else 'OFF',
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'xmlvalidationurl',
                    'name',
                ],
            },
            'xmlwsiurl_bindings': {
                'attributes_list': [
                    'xmlwsiurl',
                    'xmlwsichecks',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'xmlwsiurl',
                    'name',
                ],
            },
            'xmlxss_bindings': {
                'attributes_list': [
                    'xmlxss',
                    'isregex_xmlxss',
                    'as_scan_location_xmlxss',
                    'state',
                    'comment',
                    'name',
                ],
                'transforms': {
                    'state': lambda v: v.upper(),
                },
                'get_id_attributes': [
                    'name',
                ],
                'delete_id_attributes': [
                    'xmlxss',
                    'as_scan_location_xmlxss',
                    'name',
                ],
            },

        }

        self.module_result = dict(
            changed=False,
            failed=False,
            loglines=loglines,
        )

    def update_or_create(self):
        log('ModuleExecutor.update_or_create()')
        # Check if main object exists
        config = NitroResourceConfig(
            module=self.module,
            resource=self.main_nitro_class,
            attribute_values_dict=self.module.params,
            attributes_list=self.attribute_config[self.main_nitro_class]['attributes_list'],
            transforms=self.attribute_config[self.main_nitro_class]['transforms'],
        )

        # Create or update main object
        try:
            appfw_profile_exists = config.exists(get_id_attributes=self.attribute_config[self.main_nitro_class]['get_id_attributes'])
        except NitroException as e:
            if e.errorcode == 258:
                appfw_profile_exists = False
            else:
                raise

        if not appfw_profile_exists:
            self.module_result['changed'] = True
            if not self.module.check_mode:
                log('Appfw profile does not exist. Will create.')
                config.create()
        else:
            if not config.values_subgroup_of_actual():
                log('Existing appfw profile does not have identical values to configured. Will update.')
                self.module_result['changed'] = True
                if not self.module.check_mode:
                    config.update(id_attribute='name')

        self.sync_bindings()

    def delete(self):
        log('ModuleExecutor.delete()')
        # Check if main object exists
        config = NitroResourceConfig(
            module=self.module,
            resource=self.main_nitro_class,
            attribute_values_dict=self.module.params,
            attributes_list=self.attribute_config[self.main_nitro_class]['attributes_list'],
            transforms=self.attribute_config[self.main_nitro_class]['transforms'],
        )

        try:
            appfw_profile_exists = config.exists(get_id_attributes=self.attribute_config[self.main_nitro_class]['get_id_attributes'])
        except NitroException as e:
            if e.errorcode == 258:
                appfw_profile_exists = False
            else:
                raise

        if appfw_profile_exists:
            self.module_result['changed'] = True
            if not self.module.check_mode:
                config.delete(delete_id_attributes=self.attribute_config[self.main_nitro_class]['delete_id_attributes'])

    def sync_binding_with_data(self, data):

        binding_key = data['binding_key']
        binding_object = data['binding_object']

        if self.module.params.get(binding_key) is None:
            return

        log('ModuleExecutor syncing binding %s' % binding_key)

        mode = self.module.params[binding_key]['mode']

        # Get the existing bindings
        get_id = self.module.params[data['get_all_id']]

        try:
            existing_binding_values_dicts = NitroResourceConfig.get_all(self.module, binding_object, id=get_id)
        except NitroException as e:
            if e.errorcode == 258:
                log('Parent profile does not exist. Nothing to do for binding.')
                return
            else:
                raise

        log('existing_binding_values_dicts %s' % existing_binding_values_dicts)

        # Make a list of config objects for configured bindings
        configured_bindings = []
        for bind_values in self.module.params[binding_key]['attributes']:
            all_bind_values = copy.deepcopy(bind_values)
            main_value = self.module.params[data['link_to_main']['main_key']]
            all_bind_values.update({data['link_to_main']['bind_key']: main_value})
            configured_binding = NitroResourceConfig(
                module=self.module,
                resource=binding_object,
                attribute_values_dict=all_bind_values,
                attributes_list=self.attribute_config[binding_key]['attributes_list'],
                transforms=self.attribute_config[binding_key]['transforms'],
            )

            configured_bindings.append(configured_binding)

        # First get the existing bindings
        configured_already_present = []
        if mode == 'exact':
            # Delete any binding that is not exactly as the configured
            for existing_binding_values_dict in existing_binding_values_dicts:
                for configured_binding in configured_bindings:
                    if configured_binding.values_identical_to_dict(existing_binding_values_dict):
                        configured_already_present.append(configured_binding)
                        break
                else:
                    log('Will delete binding')
                    config = NitroResourceConfig(
                        module=self.module,
                        resource=binding_object,
                        attributes_list=self.attribute_config[binding_key]['attributes_list'],
                        transforms=self.attribute_config[binding_key]['transforms'],
                        actual_dict=existing_binding_values_dict,
                    )
                    self.module_result['changed'] = True
                    if not self.module.check_mode:
                        config.delete(delete_id_attributes=self.attribute_config[binding_key]['delete_id_attributes'])

            # Create the bindings objects that we marked in previous loop
            for configured_binding in configured_bindings:
                dict_values = [item.values_dict for item in configured_already_present]
                log('dict values %s' % dict_values)
                log('configured dict values %s' % configured_binding.values_dict)
                if configured_binding.values_dict in dict_values:
                    log('Configured binding already exists')
                    continue
                else:
                    log('Configured binding does not already exist')
                self.module_result['changed'] = True
                if not self.module.check_mode:
                    configured_binding.create()

        elif mode == 'bind':
            for configured_binding in configured_bindings:
                create_configured_binding = True
                for existing_binding_values_dict in existing_binding_values_dicts:
                    if configured_binding.values_by_key_identical_to_dict(
                            values_dict=existing_binding_values_dict,
                            key_list=self.attribute_config[binding_key]['delete_id_attributes']
                    ):
                        # Delete if not identical to all defined attributes
                        if not configured_binding.values_identical_to_dict(
                            values_dict=existing_binding_values_dict,
                        ):
                            self.module_result['changed'] = True
                            if not self.module.check_mode:
                                config = NitroResourceConfig(
                                    module=self.module,
                                    resource=binding_object,
                                    attributes_list=self.attribute_config[binding_key]['attributes_list'],
                                    transforms=self.attribute_config[binding_key]['transforms'],
                                    actual_dict=existing_binding_values_dict,
                                )
                                config.delete(delete_id_attributes=self.attribute_config[binding_key]['delete_id_attributes'])
                        else:
                            create_configured_binding = False
                if create_configured_binding:
                    self.module_result['changed'] = True
                    if not self.module.check_mode:
                        configured_binding.create()

        elif mode == 'unbind':
            for configured_binding in configured_bindings:
                for existing_binding_values_dict in existing_binding_values_dicts:
                    if configured_binding.values_by_key_identical_to_dict(
                            values_dict=existing_binding_values_dict,
                            key_list=self.attribute_config[binding_key]['delete_id_attributes']
                    ):
                        self.module_result['changed'] = True
                        if not self.module.check_mode:
                            configured_binding.delete(delete_id_attributes=self.attribute_config[binding_key]['delete_id_attributes'])

    def sync_bindings(self):
        log('ModuleExecutor.sync_bindings()')

        self.sync_contenttype_bindings()
        self.sync_cookieconsistency_bindings()
        self.sync_creditcardnumber_bindings()
        self.sync_crosssitescripting_bindings()
        self.sync_csrftag_bindings()
        self.sync_denyurl_bindings()
        self.sync_excluderescontenttype_bindings()
        self.sync_fieldconsistency_bindings()
        self.sync_fieldformat_bindings()
        self.sync_safeobject_bindings()
        self.sync_sqlinjection_bindings()
        self.sync_starturl_bindings()
        self.sync_trustedlearningclients_bindings()
        self.sync_xmlattachmenturl_bindings()
        self.sync_xmldosurl_bindings()
        self.sync_xmlsqlinjection_bindings()
        self.sync_xmlvalidationurl_bindings()
        self.sync_xmlwsiurl_bindings()
        self.sync_xmlxss_bindings()

    def sync_contenttype_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'contenttype_bindings',
                'binding_object': 'appfwprofile_contenttype_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def sync_cookieconsistency_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'cookieconsistency_bindings',
                'binding_object': 'appfwprofile_cookieconsistency_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def sync_creditcardnumber_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'creditcardnumber_bindings',
                'binding_object': 'appfwprofile_creditcardnumber_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def sync_crosssitescripting_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'crosssitescripting_bindings',
                'binding_object': 'appfwprofile_crosssitescripting_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def sync_csrftag_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'csrftag_bindings',
                'binding_object': 'appfwprofile_csrftag_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def sync_denyurl_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'denyurl_bindings',
                'binding_object': 'appfwprofile_denyurl_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def sync_excluderescontenttype_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'excluderescontenttype_bindings',
                'binding_object': 'appfwprofile_excluderescontenttype_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def sync_fieldconsistency_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'fieldconsistency_bindings',
                'binding_object': 'appfwprofile_fieldconsistency_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def sync_fieldformat_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'fieldformat_bindings',
                'binding_object': 'appfwprofile_fieldformat_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def sync_safeobject_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'safeobject_bindings',
                'binding_object': 'appfwprofile_safeobject_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def sync_sqlinjection_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'sqlinjection_bindings',
                'binding_object': 'appfwprofile_sqlinjection_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def sync_starturl_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'starturl_bindings',
                'binding_object': 'appfwprofile_starturl_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def sync_trustedlearningclients_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'trustedlearningclients_bindings',
                'binding_object': 'appfwprofile_trustedlearningclients_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def sync_xmlattachmenturl_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'xmlattachmenturl_bindings',
                'binding_object': 'appfwprofile_xmlattachmenturl_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def sync_xmldosurl_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'xmldosurl_bindings',
                'binding_object': 'appfwprofile_xmldosurl_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def sync_xmlsqlinjection_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'xmlsqlinjection_bindings',
                'binding_object': 'appfwprofile_xmlsqlinjection_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def sync_xmlvalidationurl_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'xmlvalidationurl_bindings',
                'binding_object': 'appfwprofile_xmlvalidationurl_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def sync_xmlwsiurl_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'xmlwsiurl_bindings',
                'binding_object': 'appfwprofile_xmlwsiurl_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def sync_xmlxss_bindings(self):
        self.sync_binding_with_data(
            {
                'binding_key': 'xmlxss_bindings',
                'binding_object': 'appfwprofile_xmlxss_binding',
                'get_all_id': 'name',
                'link_to_main': {
                    'main_key': 'name',
                    'bind_key': 'name',
                }
            }
        )

    def main(self):
        try:

            if self.module.params['state'] == 'present':
                self.update_or_create()
            elif self.module.params['state'] == 'absent':
                self.delete()

            self.module.exit_json(**self.module_result)

        except NitroException as e:
            msg = "nitro exception errorcode=%s, message=%s, severity=%s" % (str(e.errorcode), e.message, e.severity)
            self.module.fail_json(msg=msg, **self.module_result)
        except Exception as e:
            msg = 'Exception %s: %s' % (type(e), str(e))
            self.module.fail_json(msg=msg, **self.module_result)


def main():

    argument_spec = dict()

    module_specific_arguments = dict(

        name=dict(type='str'),

        defaults=dict(
            type='str',
            choices=[
                'basic',
                'advanced',
            ]
        ),
        starturlaction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'learn',
                'log',
                'stats',
            ]
        ),
        contenttypeaction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'learn',
                'log',
                'stats',
            ]
        ),
        inspectcontenttypes=dict(
            type='list',
            choices=[
                'none',
                'application/x-www-form-urlencoded',
                'multipart/form-data',
                'text/x-gwt-rpc',
            ]
        ),
        starturlclosure=dict(type='bool'),

        denyurlaction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'learn',
                'log',
                'stats',
            ]
        ),
        refererheadercheck=dict(
            type='str',
            choices=[
                'OFF',
                'if_present',
                'AlwaysExceptStartURLs',
                'AlwaysExceptFirstRequest',
            ]
        ),
        cookieconsistencyaction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'learn',
                'log',
                'stats',
            ]
        ),
        cookietransforms=dict(type='bool'),

        cookieencryption=dict(
            type='str',
            choices=[
                'none',
                'decryptOnly',
                'encryptSessionOnly',
                'encryptAll',
            ]
        ),
        cookieproxying=dict(
            type='str',
            choices=[
                'none',
                'sessionOnly',
            ]
        ),
        addcookieflags=dict(
            type='str',
            choices=[
                'none',
                'httpOnly',
                'secure',
                'all',
            ]
        ),
        fieldconsistencyaction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'learn',
                'log',
                'stats',
            ]
        ),
        csrftagaction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'learn',
                'log',
                'stats',
            ]
        ),
        crosssitescriptingaction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'learn',
                'log',
                'stats',
            ]
        ),
        crosssitescriptingtransformunsafehtml=dict(type='bool'),

        crosssitescriptingcheckcompleteurls=dict(type='bool'),

        sqlinjectionaction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'learn',
                'log',
                'stats',
            ]
        ),
        sqlinjectiontransformspecialchars=dict(type='bool'),

        sqlinjectiononlycheckfieldswithsqlchars=dict(type='bool'),

        sqlinjectiontype=dict(
            type='str',
            choices=[
                'SQLSplChar',
                'SQLKeyword',
                'SQLSplCharORKeyword',
                'SQLSplCharANDKeyword',
            ]
        ),
        sqlinjectionchecksqlwildchars=dict(type='bool'),

        fieldformataction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'learn',
                'log',
                'stats',
            ]
        ),
        defaultfieldformattype=dict(type='str'),

        defaultfieldformatminlength=dict(type='str'),

        defaultfieldformatmaxlength=dict(type='str'),

        bufferoverflowaction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'learn',
                'log',
                'stats',
            ]
        ),
        bufferoverflowmaxurllength=dict(type='str'),

        bufferoverflowmaxheaderlength=dict(type='str'),

        bufferoverflowmaxcookielength=dict(type='str'),

        creditcardaction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'learn',
                'log',
                'stats',
            ]
        ),
        creditcard=dict(
            type='list',
            choices=[
                'none',
                'visa',
                'mastercard',
                'discover',
                'amex',
                'jcb',
                'dinersclub',
            ]
        ),
        creditcardmaxallowed=dict(type='str'),

        creditcardxout=dict(type='bool'),

        dosecurecreditcardlogging=dict(type='bool'),

        streaming=dict(type='bool'),

        trace=dict(type='bool'),

        requestcontenttype=dict(type='str'),

        responsecontenttype=dict(type='str'),

        xmldosaction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'learn',
                'log',
                'stats',
            ]
        ),
        xmlformataction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'learn',
                'log',
                'stats',
            ]
        ),
        xmlsqlinjectionaction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'learn',
                'log',
                'stats',
            ]
        ),
        xmlsqlinjectiononlycheckfieldswithsqlchars=dict(type='bool'),

        xmlsqlinjectiontype=dict(
            type='str',
            choices=[
                'SQLSplChar',
                'SQLKeyword',
                'SQLSplCharORKeyword',
                'SQLSplCharANDKeyword',
            ]
        ),
        xmlsqlinjectionchecksqlwildchars=dict(type='bool'),

        xmlsqlinjectionparsecomments=dict(
            type='str',
            choices=[
                'checkall',
                'ansi',
                'nested',
                'ansinested',
            ]
        ),
        xmlxssaction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'learn',
                'log',
                'stats',
            ]
        ),
        xmlwsiaction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'learn',
                'log',
                'stats',
            ]
        ),
        xmlattachmentaction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'learn',
                'log',
                'stats',
            ]
        ),
        xmlvalidationaction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'learn',
                'log',
                'stats',
            ]
        ),
        xmlerrorobject=dict(type='str'),

        customsettings=dict(type='str'),

        signatures=dict(type='str'),

        xmlsoapfaultaction=dict(
            type='list',
            choices=[
                'none',
                'block',
                'log',
                'remove',
                'stats',
            ]
        ),
        usehtmlerrorobject=dict(type='bool'),

        errorurl=dict(type='str'),

        htmlerrorobject=dict(type='str'),

        logeverypolicyhit=dict(type='bool'),

        stripcomments=dict(type='bool'),

        striphtmlcomments=dict(
            type='str',
            choices=[
                'none',
                'all',
                'exclude_script_tag',
            ]
        ),
        stripxmlcomments=dict(
            type='str',
            choices=[
                'none',
                'all',
            ]
        ),
        exemptclosureurlsfromsecuritychecks=dict(type='bool'),

        defaultcharset=dict(type='str'),

        postbodylimit=dict(type='str'),

        fileuploadmaxnum=dict(type='str'),

        canonicalizehtmlresponse=dict(type='bool'),

        enableformtagging=dict(type='bool'),

        sessionlessfieldconsistency=dict(
            type='str',
            choices=[
                'OFF',
                'ON',
                'postOnly',
            ]
        ),
        sessionlessurlclosure=dict(type='bool'),

        semicolonfieldseparator=dict(type='bool'),

        excludefileuploadfromchecks=dict(type='bool'),

        sqlinjectionparsecomments=dict(
            type='str',
            choices=[
                'checkall',
                'ansi',
                'nested',
                'ansinested',
            ]
        ),
        invalidpercenthandling=dict(
            type='str',
            choices=[
                'apache_mode',
                'asp_mode',
                'secure_mode',
            ]
        ),
        type=dict(
            type='list',
            choices=[
                'HTML',
                'XML',
            ]
        ),
        checkrequestheaders=dict(type='bool'),

        optimizepartialreqs=dict(type='bool'),

        urldecoderequestcookies=dict(type='bool'),

        comment=dict(type='str'),

        percentdecoderecursively=dict(type='bool'),

        multipleheaderaction=dict(
            type='list',
            choices=[
                'block',
                'keepLast',
                'log',
                'none',
            ]
        ),
        archivename=dict(type='str'),


        contenttype_bindings=dict(type='dict'),
        cookieconsistency_bindings=dict(type='dict'),
        creditcardnumber_bindings=dict(type='dict'),
        crosssitescripting_bindings=dict(type='dict'),
        csrftag_bindings=dict(type='dict'),
        denyurl_bindings=dict(type='dict'),
        excluderescontenttype_bindings=dict(type='dict'),
        fieldconsistency_bindings=dict(type='dict'),
        fieldformat_bindings=dict(type='dict'),
        safeobject_bindings=dict(type='dict'),
        sqlinjection_bindings=dict(type='dict'),
        starturl_bindings=dict(type='dict'),
        trustedlearningclients_bindings=dict(type='dict'),
        xmlattachmenturl_bindings=dict(type='dict'),
        xmldosurl_bindings=dict(type='dict'),
        xmlsqlinjection_bindings=dict(type='dict'),
        xmlvalidationurl_bindings=dict(type='dict'),
        xmlwsiurl_bindings=dict(type='dict'),
        xmlxss_bindings=dict(type='dict'),
    )

    argument_spec.update(netscaler_common_arguments)
    argument_spec.update(module_specific_arguments)

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    executor = ModuleExecutor(module=module)
    executor.main()


if __name__ == '__main__':
    main()
