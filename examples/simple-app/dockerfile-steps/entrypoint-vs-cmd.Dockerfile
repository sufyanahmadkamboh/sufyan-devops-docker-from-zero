# ENTRYPOINT is the fixed program. CMD is the default argument, easy to replace.
#   docker run greeter            -> Hello, world
#   docker run greeter Docker     -> Hello, Docker
FROM alpine:3.24
ENTRYPOINT ["echo", "Hello,"]
CMD ["world"]
