with import <nixpkgs> {};

mkShell {
  buildInputs = [
    antigravity-fhs
    python3
  ];
}
