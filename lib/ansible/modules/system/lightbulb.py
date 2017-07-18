def main():
    module = AnsibleModule(
        argument_spec = dict(
            name=dict(required=True)
        )
    )

    name = module.params["name"]

    print("hello world")

    module.exit_json(changed=False, name=name)

if __name__ == '__main__':
    main()
