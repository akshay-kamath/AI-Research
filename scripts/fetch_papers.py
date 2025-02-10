import feedparser
import os
import re
import requests
from datetime import datetime, timedelta
import urllib.parse

# === Base Configuration ===
BASE_URL = "http://export.arxiv.org/api/query?"
SEARCH_QUERY = (
    "large language models OR generative AI OR diffusion models OR reinforcement learning OR "
    "self-supervised learning OR instruction tuning OR retrieval-augmented generation OR "
    "scaling laws OR mixture of experts OR prompt engineering OR model distillation OR "
    "low-rank adaptation OR multi-modal learning OR AI safety OR interpretability OR "
    "long-context learning OR function calling OR AI deployment OR RLHF OR efficient inference OR "
    "alignment OR federated learning OR zero-shot learning OR continual learning OR "
    "chain-of-thought prompting OR graph neural networks OR foundation models OR "
    "causal reasoning OR out-of-distribution generalization OR fairness in AI OR "
    "privacy-preserving AI OR robustness OR adversarial AI OR responsible AI OR governance OR "
    "AI regulation OR model auditing OR algorithmic transparency"
)


# Encode the search query properly
encoded_query = urllib.parse.quote(SEARCH_QUERY)

# Configurable Parameters
CITATION_THRESHOLD = 0  # No filter on citation count
CURRENT_YEAR = datetime.now().year  # Dynamically update year
OUTPUT_DIR = f"research_updates/{CURRENT_YEAR}_papers"
ARXIV_FEED_URL = f"{BASE_URL}search_query=all:{encoded_query}&start=0&max_results=50&sortBy=submittedDate&sortOrder=descending"

# === Expanded Topic Tags ===
TOPIC_TAGS = {
    "LLM": ["large language model", "transformer", "bert", "gpt", "t5", "mistral", "llama", "phi", "gemini", "mixtral", "moe", "sft"],
    "Diffusion Models": ["diffusion", "stable diffusion", "denoising", "image generation", "text-to-image"],
    "RLHF": ["reinforcement learning", "human feedback", "reward model", "policy optimization", "rlhf", "alignment"],
    "Multimodal AI": ["multimodal", "vision-language", "speech-to-text", "audio", "video","clip", "flamingo", "blip"],
    "Optimization": ["fine-tuning", "quantization", "pruning", "optimization","inference optimization", "low-rank adaptation", "LoRA","distillation", "lora", "adapter"],
    "Scaling Laws": ["scaling", "mixture of experts", "MoE", "large-scale training", "distributed training"],
    "Training & Evaluation": ["benchmarking", "evaluation", "perplexity", "loss function", "in-context learning"],    
    "Model Evaluation": ["benchmarking", "hallucination", "toxicity", "robustness", "trustworthiness", "bias"],
    "Production and Deployment": ["latency", "serving llms","model serving", "latency reduction", "edge AI", "serverless AI","gpu optimization", "tpu"],
    "Prompt Engineering": ["prompt tuning", "function calling","prompt tuning", "zero-shot", "few-shot", "instruction tuning", "chain-of-thought", "cot"],
    "AI Safety": ["interpretability", "factual consistency", "adversarial attacks"],
    "Graph AI": ["graph neural networks", "GNN", "knowledge graphs", "reasoning over graphs"],
    "Ongoing Learning": ["zero-shot learning", "few-shot learning", "continual learning", "out-of-distribution"],
    "Responsible AI": ["fairness","bias","bias mitigation","hallucinations", "privacy-preserving AI", "robustness", "AI ethics","adversarial AI", "governance", "algorithmic transparency", "AI regulation", "model auditing"],
    "Autonomous Agents": ["auto-gpt", "babyagi", "autogen","crew ai" "agentic workflows","agentic ai","ai agents"],
    "Memory & Context Length": ["long context", "attention span", "context window"],
    "Security & Adversarial ML": ["prompt injection", "jailbreak", "security", "adversarial attacks", "cybersecurity"],
    "LLM Ops": ["LLMOps", "MLOps for LLMs", "model deployment", "model serving", "serverless LLMs","model versioning", "A/B testing for LLMs", "continuous integration for AI","observability", "monitoring LLMs", "model logging", "prompt engineering best practices"], 
    "RAG": ["retrieval-augmented generation", "vector databases", "semantic search","hybrid search", "knowledge grounding", "document retrieval", "LLM + databases","memory-augmented models", "knowledge-enhanced generation"],
    "Fine-Tuning": ["RLHF (Reinforcement Learning with Human Feedback)", "human feedback tuning","contrastive learning", "instruction tuning", "reward models", "supervised fine-tuning","pretraining strategies", "self-supervised learning", "PEFT"]
}

def classify_paper(title, summary):
    """
    Assigns tags to a research paper based on its title and summary.
    """
    tags = set()
    for topic, keywords in TOPIC_TAGS.items():
        for keyword in keywords:
            if re.search(rf"\b{keyword}\b", title, re.IGNORECASE) or re.search(rf"\b{keyword}\b", summary, re.IGNORECASE):
                tags.add(topic)
    return list(tags) if tags else ["General AI"]

def get_citation_count(arxiv_id):
    """
    Fetch citation count from Semantic Scholar API (if available).
    """
    try:
        response = requests.get(f"https://api.semanticscholar.org/v1/paper/arXiv:{arxiv_id}")
        data = response.json()
        return data.get("citationCount", 0)
    except:
        return 0  # Default if API call fails

def fetch_papers():
    """
    Fetches the latest AI research papers from ArXiv.
    """
    feed = feedparser.parse(ARXIV_FEED_URL)
    papers = []

    print(f"📥 Found {len(feed.entries)} papers in the ArXiv feed.")

    for entry in feed.entries:
        arxiv_id = entry.id.split("/abs/")[-1]  # Extract ArXiv ID
        citation_count = get_citation_count(arxiv_id)  # Fetch citation count

        print(f"🔍 Processing: {entry.title}")
        print(f"   🆔 ID: {arxiv_id}, 📈 Citations: {citation_count}")

        if citation_count < CITATION_THRESHOLD:
            print(f"   ⏩ Skipping (below citation threshold)")
            continue  # Skip papers below the citation threshold

        tags = classify_paper(entry.title, entry.summary)
        full_summary = entry.summary.replace("\n", " ")  # Preserve full abstract

        paper = {
            "title": entry.title,
            "authors": ", ".join(author.name for author in entry.authors),
            "published": entry.published.split("T")[0],
            "summary": full_summary,
            "link": entry.link,
            "tags": ", ".join(tags),
            "citations": citation_count
        }
        papers.append(paper)

    print(f"✅ Total papers after filtering: {len(papers)}")
    return papers

def get_week_date_range():
    """Returns the Monday-Sunday range for the previous week"""
    today = datetime.today()
    last_monday = today - timedelta(days=today.weekday() + 7)
    last_sunday = last_monday + timedelta(days=6)
    return last_monday.strftime("%B%d"), last_sunday.strftime("%B%d"), last_monday.year

def save_markdown(papers):
    """
    Saves fetched papers into a Markdown file, categorized by field, with correct weekly date format.
    """
    #os.makedirs(OUTPUT_DIR, exist_ok=True)

    start_date, end_date,year = get_week_date_range()
    # Dynamic output directory based on year
    output_dir = f"research_updates/{year}_papers"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(OUTPUT_DIR, f"{start_date}_to_{end_date}.md")

    if not papers:
        print("⚠️ No papers to write. Check filters!")
        return

    print(f"📝 Writing {len(papers)} papers to {file_path}")

    categorized_papers = {topic: [] for topic in TOPIC_TAGS.keys()}
    categorized_papers["General AI"] = []

    for paper in papers:
        topic = paper["tags"].split(", ")[0]
        categorized_papers[topic].append(paper)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# 📌 AI Research Papers ({start_date} to {end_date})\n\n")

        for category, papers_list in categorized_papers.items():
            if not papers_list:
                continue

            f.write(f"## 🔹 {category}\n\n")
            f.write("| 📄 Title | 🖊 Authors | 📅 Date | 🏷 Tags | 📜 Summary | 🔗 Link |\n")
            f.write("|---------|---------|---------|---------|---------|---------|\n")

            for paper in papers_list:
                formatted_summary = paper["summary"].replace("|", " ")
                f.write(f"| [{paper['title']}]({paper['link']}) | {paper['authors']} | {paper['published']} | {paper['tags']} | {formatted_summary} | [🔗 Paper]({paper['link']}) |\n")

    print(f"✅ Papers saved to {file_path}")

# Run the script
if __name__ == "__main__":
    papers = fetch_papers()
    save_markdown(papers)
