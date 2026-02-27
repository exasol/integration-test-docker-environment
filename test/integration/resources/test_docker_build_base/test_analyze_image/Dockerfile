FROM ubuntu:22.04

#As workaround we also copy Dockerfile because my_package_file.yaml may or may not exist
#If it does not exist, COPY would throw an error because it would not find any source file.
COPY Dockerfile my_package_file.yaml* /