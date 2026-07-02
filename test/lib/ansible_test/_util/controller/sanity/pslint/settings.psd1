@{
    Rules = @{
        PSAvoidLongLines = @{
            Enable = $true
            MaximumLineLength = 160
        }
        PSAvoidSemicolonsAsLineTerminators = @{
            Enable = $true
        }
        PSPlaceOpenBrace = @{
            Enable = $true
            OnSameLine = $true
            IgnoreOneLineBlock = $true
            NewLineAfter = $true
        }
        PSPlaceCloseBrace = @{
            Enable = $true
            IgnoreOneLineBlock = $true
            NewLineAfter = $true
            NoEmptyLineBefore = $false
        }
        PSUseConsistentIndentation = @{
            Enable = $true
            IndentationSize = 4
            PipelineIndentation = 'IncreaseIndentationForFirstPipeline'
            Kind = 'space'
        }
        PSUseConsistentWhitespace = @{
            Enable = $true
            CheckInnerBrace = $true
            CheckOpenBrace = $true
            CheckOpenParen = $true
            CheckOperator = $true
            CheckPipe = $true
            CheckPipeForRedundantWhitespace = $false
            CheckSeparator = $true
            CheckParameter = $false
            IgnoreAssignmentOperatorInsideHashTable = $false
        }
    }
    ExcludeRules = @(
        'PSUseOutputTypeCorrectly',
        'PSUseShouldProcessForStateChangingFunctions',
        # We send strings as plaintext so will always come across the 3 issues
        'PSAvoidUsingPlainTextForPassword',
        'PSAvoidUsingConvertToSecureStringWithPlainText',
        'PSAvoidUsingUserNameAndPassWordParams',
        # We send the module as a base64 encoded string and a BOM will cause
        # issues here
        'PSUseBOMForUnicodeEncodedFile',
        # Too many false positives, there are many cases where shared utils
        # invoke user defined code but not all parameters are used.
        'PSReviewUnusedParameter'
    )
}
