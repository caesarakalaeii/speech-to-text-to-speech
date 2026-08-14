{
  description = "speech-to-text-to-speech -- local speech in, a different voice out";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];

      forAllSystems = f:
        nixpkgs.lib.genAttrs systems
          (system: f nixpkgs.legacyPackages.${system});

      # Python 3.13, matching `.python-version` so uv and nix agree on the
      # interpreter. Below the nixpkgs default of 3.14, which pyproject.toml
      # excludes (`requires-python = ">=3.10,<3.14"`).
      #
      # Do not "fix" this to 3.12: nixpkgs has no cached onnxruntime for 3.12,
      # so that build pulls protobuf, eigen and a Rust toolchain from source.
      #
      # kokoro-onnx and espeakng-loader are absent from nixpkgs, so the
      # synthesiser is not importable from this environment. It does not have
      # to be: stts.tts imports them lazily inside Synthesiser._load(), so
      # every unit test collects and runs, and the e2e tests skip on their
      # models fixture. See the devShell for the uv-based route that does get
      # the synthesiser.
      pythonFor = pkgs: pkgs.python313.withPackages (ps: [
        ps.numpy # everywhere
        ps.scipy # audio/resample.py
        ps.onnxruntime # vad.py, runtime.py
        ps.sounddevice # audio/capture.py, audio/playback.py (lazy)
        ps.onnx-asr # stt.py (lazy)
        ps.huggingface-hub # models.py (lazy) -- the [hub] extra
        ps.pytest
        ps.pytest-timeout # pyproject sets timeout = 600
      ]);
    in
    {
      # `nix flake check`, or `nix build .#checks.<system>.unit-tests`
      #
      # Runs the suite hermetically. The 8 end-to-end tests skip themselves:
      # they need ~870 MB of ONNX models that a build sandbox has no business
      # downloading, so what this gate proves is the 57 unit tests.
      checks = forAllSystems (pkgs: {
        unit-tests = pkgs.runCommand "stts-unit-tests"
          {
            nativeBuildInputs = [ (pythonFor pkgs) ];
            src = self;
          }
          ''
            cp -r "$src" work && chmod -R u+w work && cd work

            # paths.data_dir() mkdirs under $XDG_DATA_HOME, and
            # models.all_ready() calls it while deciding whether to skip.
            # Both need somewhere writable.
            export HOME="$(mktemp -d)"
            export XDG_DATA_HOME="$HOME/.local/share"

            # Deliberately not piped into tee: a pipeline's status is the last
            # command's, so `pytest | tee` would report success for a failing
            # suite unless pipefail happens to be set.
            if ! python -m pytest -p no:cacheprovider -q > result.txt 2>&1; then
              cat result.txt
              exit 1
            fi
            cat result.txt

            mkdir -p "$out"
            cp result.txt "$out/"
          '';
      });

      # `nix develop`, then `pytest`.
      #
      # uv is here for the one thing nixpkgs cannot cover: kokoro-onnx and
      # espeakng-loader are not packaged, so the synthesiser -- and with it the
      # e2e tests -- needs `uv sync --group dev` and `uv run stts setup`.
      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = [ (pythonFor pkgs) pkgs.uv ]
            ++ pkgs.lib.optionals pkgs.stdenv.hostPlatform.isLinux [
            pkgs.portaudio # sounddevice dlopens this
            pkgs.espeak-ng # kokoro-onnx phonemises through it
          ];

          shellHook = ''
            echo "speech-to-text-to-speech dev shell"
            echo "  pytest               -- 57 unit tests (e2e skip without models)"
            echo "  uv sync --group dev  -- add kokoro-onnx for the e2e path"
            echo
          '';
        };
      });

      # The interpreter plus test dependencies, exposed so CI can reuse it.
      packages = forAllSystems (pkgs: { default = pythonFor pkgs; });
    };
}
