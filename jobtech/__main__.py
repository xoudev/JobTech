"""Point d'entrée CLI :  python -m jobtech <commande>

  collect   Lance la collecte de toutes les sources configurées
  serve     Démarre l'interface web de recherche
  stats     Affiche les statistiques de la base
"""
from __future__ import annotations

import argparse
import json
import logging


def _setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")


def cmd_collect(_args: argparse.Namespace) -> None:
    from . import pipeline

    recap = pipeline.run_collection()
    total_new = sum(r.get("new", 0) for r in recap.values())
    print("\n=== Récapitulatif ===")
    for name, r in recap.items():
        print(f"  {name:16} {r['status']:8} +{r.get('new', 0)} nouvelles")
    print(f"Total : {total_new} nouvelles offres.\n")


def cmd_serve(args: argparse.Namespace) -> None:
    import uvicorn

    uvicorn.run("jobtech.web.app:app", host=args.host, port=args.port, reload=args.reload)


def cmd_stats(_args: argparse.Namespace) -> None:
    from . import db

    db.init()
    print(json.dumps(db.stats(), indent=2, ensure_ascii=False))


def main() -> None:
    _setup_logging()
    parser = argparse.ArgumentParser(prog="jobtech", description="Agrégateur d'offres IT (Île-de-France)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("collect", help="Collecte les offres depuis toutes les sources").set_defaults(func=cmd_collect)

    p_serve = sub.add_parser("serve", help="Démarre l'interface web")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--reload", action="store_true")
    p_serve.set_defaults(func=cmd_serve)

    sub.add_parser("stats", help="Statistiques de la base").set_defaults(func=cmd_stats)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
