from pathlib import Path

from app.ai.ollama_provider import OllamaStructuredCompletionProvider
from app.ai.provider import LLMOrderExtractor
from benchmarks.runner import load_corpus, run_benchmark, write_report


def main() -> None:
    corpus = load_corpus(Path("benchmarks/corpus.json"))
    extractor = LLMOrderExtractor(OllamaStructuredCompletionProvider.from_env())
    report = run_benchmark(extractor, corpus)
    write_report(report, Path("benchmark-results/qwen-report.json"))
    print(Path("benchmark-results/qwen-report.json").read_text())


if __name__ == "__main__":
    main()
