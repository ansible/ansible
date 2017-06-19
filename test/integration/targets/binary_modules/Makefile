.PHONY: all clean

all:
	# Compiled versions of these binary modules are available at the url below.
	# This avoids a dependency on go and keeps the binaries out of our git repository.
	# https://ansible-ci-files.s3.amazonaws.com/test/integration/roles/test_binary_modules/
	cd library; \
	GOOS=linux   GOARCH=amd64 go build -o helloworld_linux       helloworld.go; \
	GOOS=windows GOARCH=amd64 go build -o helloworld_win32nt.exe helloworld.go; \
	GOOS=darwin  GOARCH=amd64 go build -o helloworld_darwin      helloworld.go; \
	GOOS=freebsd GOARCH=amd64 go build -o helloworld_freebsd     helloworld.go

clean:
	rm -f library/helloworld_*
