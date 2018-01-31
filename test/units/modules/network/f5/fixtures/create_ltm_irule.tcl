when RULE_INIT {
   set static::FormBaseURL "/sp-ofba-form"
   set static::FormReturnURL "/sp-ofba-completed"
   set static::HeadAuthReq "X-FORMS_BASED_AUTH_REQUIRED"
   set static::HeadAuthRet "X-FORMS_BASED_AUTH_RETURN_URL"
   set static::HeadAuthSize "X-FORMS_BASED_AUTH_DIALOG_SIZE"
   set static::HeadAuthSizeVal "800x600"
   set static::ckname "MRHSession_SP"
   set static::Basic_Realm_Text "SharePoint Authentication"
}

when HTTP_REQUEST {
    set apmsessionid [HTTP::cookie value MRHSession]
}

when HTTP_RESPONSE {
       # Insert persistent cookie for html content type and private session
}
