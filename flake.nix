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
      # The synthesiser's three dependencies that nixpkgs does not carry.
      # Building them here is what makes the app runnable from nix rather than
      # test-only: without kokoro-onnx there is no Synthesiser, and without a
      # Synthesiser there is no output voice.
      synthDeps = pkgs: ps: rec {
        # Upstream ships a vendored libespeak-ng inside a manylinux wheel.
        # Rather than patchelf a foreign binary, point the same two-function
        # API at the espeak-ng nixpkgs already builds. stts.tts only ever calls
        # get_library_path() and get_data_path().
        espeakng-loader = ps.buildPythonPackage {
          pname = "espeakng-loader";
          version = "0.2.4-nixpkgs-espeak";
          format = "other";
          dontUnpack = true;
          installPhase = ''
            mkdir -p "$out/${ps.python.sitePackages}"

            # Real dist-info, so kokoro-onnx's declared dependency on
            # espeakng-loader is genuinely satisfied rather than suppressed.
            dist="$out/${ps.python.sitePackages}/espeakng_loader-0.2.4.dist-info"
            mkdir -p "$dist"
            cat > "$dist/METADATA" <<'META'
            Metadata-Version: 2.1
            Name: espeakng-loader
            Version: 0.2.4
            Summary: Locate espeak-ng's shared library and data directory.
            META
            echo "Wheel-Version: 1.0" > "$dist/WHEEL"
            echo "espeakng_loader" > "$dist/top_level.txt"
            : > "$dist/RECORD"

            cat > "$out/${ps.python.sitePackages}/espeakng_loader.py" <<EOF
            """Shim: serve nixpkgs' espeak-ng instead of a vendored copy."""
            from pathlib import Path

            _PREFIX = Path("${pkgs.espeak-ng}")


            def get_library_path() -> Path:
                return _PREFIX / "lib" / "libespeak-ng${pkgs.stdenv.hostPlatform.extensions.sharedLibrary}"


            def get_data_path() -> Path:
                return _PREFIX / "share" / "espeak-ng-data"
            EOF
          '';
        };

        phonemizer-fork = ps.buildPythonPackage rec {
          pname = "phonemizer_fork";
          version = "3.3.2";
          format = "wheel";
          src = pkgs.fetchurl {
            url = "https://files.pythonhosted.org/packages/64/f1/0dcce21b0ae16a82df4b6583f8f3ad8e55b35f7e98b6bf536a4dd225fa08/${pname}-${version}-py3-none-any.whl";
            hash = "sha256-lzBcdvQYOzgl2uj0wDImX+eMmUbOWMR9S2IWE0kmS3Q=";
          };
          propagatedBuildInputs = [ ps.attrs ps.dlinfo ps.joblib ps.segments ps.typing-extensions ];
          doCheck = false;
          pythonImportsCheck = [ "phonemizer" ];
        };

        kokoro-onnx = ps.buildPythonPackage rec {
          pname = "kokoro_onnx";
          version = "0.5.0";
          format = "wheel";
          src = pkgs.fetchurl {
            url = "https://files.pythonhosted.org/packages/0d/55/0bfcb4aa50033c89e5ac132af3d07fac0543824ce6eaefd4d1bfdcc3795b/${pname}-${version}-py3-none-any.whl";
            hash = "sha256-Thw4opbbXbwfci9p9ePBPy4od7PlsUUof1bsBXAT41c=";
          };
          propagatedBuildInputs = [ ps.numpy ps.onnxruntime espeakng-loader phonemizer-fork ];
          doCheck = false;
          pythonImportsCheck = [ "kokoro_onnx" ];
        };
      };

      pythonFor = pkgs: pkgs.python313.withPackages (ps:
        let extra = synthDeps pkgs ps; in [
          ps.numpy # everywhere
          ps.scipy # audio/resample.py
          ps.onnxruntime # vad.py, runtime.py
          ps.sounddevice # audio/capture.py, audio/playback.py (lazy)
          ps.onnx-asr # stt.py (lazy)
          ps.huggingface-hub # models.py (lazy) -- the [hub] extra
          ps.tkinter # gui.py
          extra.kokoro-onnx # tts.py -- pulls the other two
          ps.pytest
          ps.pytest-timeout # pyproject sets timeout = 600
        ]);

      # The application itself, so `nix run` does not depend on the working
      # directory happening to be the source tree.
      sttsFor = pkgs:
        let
          ps = pkgs.python313Packages;
          extra = synthDeps pkgs ps;
        in
        ps.buildPythonApplication {
          pname = "speech-to-text-to-speech";
          version = "2.0.0";
          pyproject = true;
          src = self;
          build-system = [ ps.hatchling ];
          dependencies = [
            ps.numpy
            ps.scipy
            ps.sounddevice
            ps.onnx-asr
            ps.huggingface-hub # the onnx-asr [hub] extra
            ps.onnxruntime
            ps.tkinter # gui.py
            extra.kokoro-onnx
          ];
          # The suite is the `checks` output; running it here too would make
          # every `nix run` wait on it.
          doCheck = false;
          pythonImportsCheck = [ "stts" "stts.gui" "stts.pipeline" ];
        };
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

      # `nix develop` -- a complete environment: every runtime dependency plus
      # the test tools, so `stts setup` and the GUI both work, not just pytest.
      #
      # uv remains available for cross-checking against the locked PyPI
      # versions, which are not always the ones nixpkgs carries.
      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = [ (pythonFor pkgs) pkgs.uv ]
            ++ pkgs.lib.optionals pkgs.stdenv.hostPlatform.isLinux [
            pkgs.portaudio # sounddevice dlopens this
            pkgs.espeak-ng # what the espeakng-loader shim above points at
          ];

          shellHook = ''
            echo "speech-to-text-to-speech dev shell"
            echo "  pytest                    -- 57 unit tests, +8 e2e once models exist"
            echo "  python -m stts.cli doctor -- check the environment"
            echo "  python -m stts.cli setup  -- download ~870 MB of models"
            echo "  python -m stts.cli        -- open the GUI"
            echo
          '';
        };
      });

      # `nix run` -- the real CLI, installed rather than run out of the source
      # tree, so it works from any directory. `nix run .# setup` first: without
      # the models there is nothing to recognise or speak with.
      apps = forAllSystems (pkgs: {
        default = {
          type = "app";
          program = "${sttsFor pkgs}/bin/stts";
        };
      });

      packages = forAllSystems (pkgs: {
        default = sttsFor pkgs;
        # The interpreter plus every dependency, exposed so CI can reuse it.
        pythonEnv = pythonFor pkgs;
      });
    };
}
