import os
from huggingface_hub import InferenceClient

from agent import DummyAgent


def main():
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise ValueError(
            "HF_TOKEN not set. Set it as an environment variable.\n"
            "PowerShell: setx HF_TOKEN \"hf_...\" (then open a new terminal)"
        )

    client = InferenceClient(token=token)
    agent = DummyAgent(client)

    print(agent.run("What's the weather in London?",max_steps=8))



if __name__ == "__main__":
    main()
