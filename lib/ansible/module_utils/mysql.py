def connect(module, login_user, login_password, config_file):
    default_file = '~/.my.cnf'
    if config_file is not None:
        default_file = config_file
    
    config = {
        'host': module.params['login_host'],
        'db': 'mysql'
    }

    if module.params['login_unix_socket']:
        config['unix_socket'] = module.params['login_unix_socket']
    else:
        config['port'] = int(module.params['login_port'])

    if os.path.exists(default_file):
        config['read_default_file'] = default_file
    else:
        config['user'] = login_user
        config['passwd'] = login_password
        
    db_connection = MySQLdb.connect(**config)
    return db_connection.cursor()
