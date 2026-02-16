FROM rust:1.75-alpine as builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache musl-dev curl

# Copy Cargo files
COPY services/rules-engine/Cargo.toml ./

# Create dummy main to cache dependencies
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release
RUN rm src/main.rs

# Copy actual source
COPY services/rules-engine/src ./src

# Build for real
RUN cargo build --release

# Runtime image
FROM alpine:latest

RUN apk add --no-cache curl

WORKDIR /app

COPY --from=builder /app/target/release/avasim-rules-engine /app/

EXPOSE 8080

CMD ["/app/avasim-rules-engine"]
