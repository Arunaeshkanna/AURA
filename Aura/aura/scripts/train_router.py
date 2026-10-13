from aura.core.router_training import FineTunedRouter


def main() -> None:
    path = FineTunedRouter().train()
    print(f"Trained router saved to {path}")


if __name__ == "__main__":
    main()
