{
  description = "Cambio card game";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { nixpkgs, ...}:
    let
      system = "x86_64-linux"; #someone else can add support for other systems later
      pkgs = import nixpkgs {inherit system;};
    in{
      packages.${system}.default = 
        pkgs.python3Packages.buildPythonApplication{
          pname = "cambio";
          version = "0.1.0";
          src = ./.;
          pyproject = true;

          build-system = [pkgs.python3Packages.setuptools];
          dependencies = [pkgs.python3Packages.pygame-ce];
        };
    };
}
