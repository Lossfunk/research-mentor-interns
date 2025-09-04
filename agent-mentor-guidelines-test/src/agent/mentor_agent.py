from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun
from typing import List, Dict, Any
from ..config import Config
from ..tools.guidelines_tool import GuidelinesToolkit
import re

class ResearchMentorAgent:
    def __init__(self, config: Config):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.MODEL_NAME,
            temperature=config.TEMPERATURE,
            api_key=config.OPENAI_API_KEY
        )
        
        # Get all tools
        self.tools = GuidelinesToolkit.get_tools()
        
        # Add general web search as fallback
        self.tools.append(DuckDuckGoSearchRun())
        
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent, 
            tools=self.tools, 
            verbose=True,
            return_intermediate_steps=True,
            max_iterations=3  # Limit tool calls
        )
    
    def _create_agent(self):
        """Create the research mentor agent"""
        
        system_prompt = """You are an expert research mentor agent specializing in:
- Research problem selection and evaluation
- Research methodology and best practices  
- Academic paper review and critique
- Developing research taste and judgment
- Academic career guidance

IMPORTANT WORKFLOW:
1. ALWAYS use the `search_research_guidelines` tool to answer user questions. The tool will return a list of dictionaries with scholarly articles and other resources.
2. Search for guidance relevant to their specific question
3. Synthesize the retrieved guidelines with your knowledge
4. When you apply insights from guidelines, cite them as '[guide_id]' in your response
5. Provide specific, actionable advice

GUIDELINE SOURCES you'll be searching include:
- Hamming's research methodology principles
- Research project selection frameworks  
- Research taste development guidance
- Academic papers on research processes
- Community discussions on research best practices

Your responses should be:
- Grounded in the retrieved guidelines when available
- Specific and actionable
- Properly cited with [guide_id] references
- Comprehensive but focused

Remember: These guidelines represent hard-won wisdom from successful researchers. Use them to enhance your advice."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        return agent
    
    def get_response(self, user_query: str) -> Dict[str, Any]:
        """Get agent response to user query"""
        
        try:
            result = self.agent_executor.invoke({
                "input": user_query
            })
            
            # Extract guidelines used from the response
            guidelines_used = self._extract_guideline_citations(result["output"])
            
            # Extract tool calls made
            tool_calls = self._extract_tool_usage(result.get("intermediate_steps", []))

            # Extract sources from guidelines tool
            sources = self._extract_sources(result.get("intermediate_steps", []))
            
            # Format response with sources
            final_response = self._format_response_with_sources(result["output"], sources)

            return {
                "response": final_response,
                "guidelines_used": guidelines_used,
                "tool_calls": tool_calls,
                "sources": sources,
                "intermediate_steps": result.get("intermediate_steps", []),
                "success": True
            }
            
        except Exception as e:
            return {
                "response": f"I apologize, but I encountered an error: {str(e)}",
                "guidelines_used": [],
                "tool_calls": [],
                "intermediate_steps": [],
                "success": False,
                "error": str(e)
            }
    
    def _extract_guideline_citations(self, response: str) -> List[str]:
        """Extract guideline IDs cited in the response"""
        citations = re.findall(r'\[guide_[a-zA-Z0-9]+\]', response)
        return [cite.strip('[]') for cite in citations]
    
    def _extract_tool_usage(self, intermediate_steps: List) -> List[Dict]:
        """Extract information about which tools were used"""
        tool_usage = []
        for step in intermediate_steps:
            if hasattr(step, 'tool') or (isinstance(step, tuple) and len(step) >= 2):
                try:
                    action = step[0] if isinstance(step, tuple) else step
                    tool_name = getattr(action, 'tool', 'unknown')
                    tool_input = getattr(action, 'tool_input', {})
                    
                    tool_usage.append({
                        'tool': tool_name,
                        'input': tool_input
                    })
                except:
                    pass
        return tool_usage

    def _extract_sources(self, intermediate_steps: List) -> List[str]:
        """Extracts source URLs from the guidelines tool output."""
        sources = []
        for step in intermediate_steps:
            # step is a tuple of (AgentAction, tool_output)
            if len(step) == 2 and hasattr(step[0], 'tool') and step[0].tool == 'search_research_guidelines':
                tool_output = step[1]
                if isinstance(tool_output, list):
                    for item in tool_output:
                        if isinstance(item, dict) and 'source' in item:
                            sources.append(item['source'])
        return list(set(sources))  # Return unique sources

    def _format_response_with_sources(self, response: str, sources: List[str]) -> str:
        """Appends formatted sources to the response."""
        if not sources:
            return response

        sources_text = "\n\nSource:\n" + "\n".join(f"{i+1}. {source}" for i, source in enumerate(sources))
        return response + sources_text
