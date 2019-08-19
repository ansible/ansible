@{
    ExcludeRules=@(
        'PSUseOutputTypeCorrectly',
        'PSUseShouldProcessForStateChangingFunctions',
        # We send strings as plaintext so will always come across the 3 issues
        'PSAvoidUsingPlainTextForPassword',
        'PSAvoidUsingConvertToSecureStringWithPlainText',
        'PSAvoidUsingUserNameAndPassWordParams',
        # We send the module as a base64 encoded string and a BOM will cause
        # issues here
        'PSUseBOMForUnicodeEncodedFile'
    )
}
