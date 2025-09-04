from src.config import Config
from src.agent.mentor_agent import ResearchMentorAgent

def setup_system():
    """Initialize the research mentor agent system"""
    print("🚀 Setting up Research Mentor Agent...")
    
    # Load configuration
    config = Config()
    
    # Create agent (no complex setup needed!)
    agent = ResearchMentorAgent(config)
    
    print("✅ Research Mentor Agent ready!")
    print(f"📚 Configured to search {len(config.GUIDELINE_SOURCES)} guideline sources")
    return agent, config

def main():
    """Main application loop"""
    agent, config = setup_system()
    
    print("\n🤖 Research Mentor Agent")
    print("Ask me about research methodology, choosing problems, developing taste, etc.")
    print("I'll search through curated research guidance sources to help you.")
    print("Type 'quit' to exit\n")
    
    while True:
        user_input = input("\n👤 You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("👋 Goodbye!")
            break
        
        if not user_input:
            continue
        
        print("\n🤖 Agent: Searching guidelines and thinking...")
        result = agent.get_response(user_input)
        
        if result["success"]:
            print(f"\n🤖 Agent: {result['response']}")
        else:
            print(f"\n❌ Error: {result['error']}")

if __name__ == "__main__":
    main()




