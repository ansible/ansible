''' Checks that the consul agent is running locally. '''

if __name__ == '__main__':

    try:
        import consul
        consul = consul.Consul(host='0.0.0.0', port=8500)
        consul.catalog.nodes()
        print("True")
    except Exception:
        pass
