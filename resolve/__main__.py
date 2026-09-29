"""Command line: python -m resolve <command>

  build [--tier public|research|all] [--k 5]   run the pipeline and write releases
  gazetteer                                    regenerate ref/localities.csv from COD-AB
  raw-manifest                                 record hashes of raw inputs (after adding a raw version)
  serve [--tier public|research] [--port N]    local web server for the map
  metrics                                      measure the public release (see docs/metrics.md)
  docs                                         regenerate docs/data-dictionary.md
"""
import argparse
import json
import sys


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="resolve")
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    b.add_argument("--tier", choices=["public", "research", "all"], default="all")
    b.add_argument("--k", type=int, default=5)
    sub.add_parser("gazetteer")
    sub.add_parser("raw-manifest")
    s = sub.add_parser("serve")
    s.add_argument("--tier", choices=["public", "research"], default="research")
    s.add_argument("--port", type=int, default=8000)
    sub.add_parser("metrics")
    sub.add_parser("docs")
    args = parser.parse_args(argv)

    if args.command == "build":
        from .publish import build
        print(json.dumps(build(args.tier, args.k), ensure_ascii=False, indent=1))
    elif args.command == "gazetteer":
        from .gazetteer import build_localities
        print(f"{build_localities()} localities written to ref/localities.csv")
    elif args.command == "raw-manifest":
        from .rawstore import write_manifest
        print(f"{write_manifest()} raw files recorded in raw/manifest.sha256")
    elif args.command == "serve":
        from .serve import serve
        serve(args.tier, args.port)
    elif args.command == "metrics":
        from .metrics import measure
        print(json.dumps(measure(), ensure_ascii=False, indent=1))
    elif args.command == "docs":
        from .docs import write_data_dictionary
        print(write_data_dictionary())


if __name__ == "__main__":
    main()
