BUF := docker run --rm --user $$(id -u):$$(id -g) -e HOME=/tmp -v $(CURDIR):/workspace -w /workspace bufbuild/buf:1.75.0

.PHONY: proto breaking

proto:
	$(BUF) lint
	$(BUF) generate
	$(BUF) build -o gen/descriptor.binpb

breaking:
	$(BUF) breaking --against '.git#branch=main'
