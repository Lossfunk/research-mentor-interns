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
    print("Type 'quit' to exit, 'cost' for usage stats, 'cache' for cache stats\n")
    
    while True:
        user_input = input("\n👤 You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("👋 Goodbye!")
            break
        
        if user_input.lower() == 'cost':
            cost_summary = agent.cost_monitor.get_cost_summary()
            print(f"\n💰 Cost Summary:")
            print(f"   Total Cost: ${cost_summary['total_cost']}")
            print(f"   Sessions: {cost_summary['session_count']}")
            print(f"   Avg per Session: ${cost_summary['avg_cost_per_session']}")
            print(f"   Est. Monthly: ${cost_summary['estimated_monthly_cost']}")
            continue
        
        if user_input.lower() == 'cache':
            cache_stats = agent.cache.get_stats()
            print(f"\n💾 Cache Stats:")
            print(f"   Total Entries: {cache_stats['total_entries']}")
            print(f"   Valid Entries: {cache_stats['valid_entries']}")
            print(f"   Hit Rate: {cache_stats['cache_hit_rate']}")
            continue
        
        if not user_input:
            continue
        
        print("\n🤖 Agent: Searching guidelines and thinking...")
        result = agent.get_response(user_input)
        
        if result["success"]:
            print(f"\n🤖 Agent: {result['response']}")
            if result.get('cached'):
                print("💰 (This response was served from cache - no API cost!)")
        else:
            print(f"\n❌ Error: {result['error']}")

if __name__ == "__main__":
    main()




