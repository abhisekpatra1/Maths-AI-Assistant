"""
Orchestrator Agent - Central Controller
Routes requests to specialized agents and manages workflow
"""

from typing import List, Dict
from loguru import logger
from langchain_google_genai import ChatGoogleGenerativeAI  
from langchain_core.prompts import ChatPromptTemplate
from agents.document_loader import DocumentLoaderAgent
from agents.qa_agent import QAAgent
from agents.extraction_agent import ExtractionAgent
from agents.report_agent import ReportAssemblyAgent
from agents.summarization_agent import SummarizationAgent
from services.vector_store import VectorStoreService
from services.session_manager import SessionManager
# import google.generativeai as genai


class OrchestratorAgent:
    """
    Central orchestrator that coordinates all specialized agents
    Decides which agent to invoke based on user intent
    """
    
    def __init__(self, vector_store: VectorStoreService, session_manager: SessionManager):
        self.vector_store = vector_store
        self.session_manager = session_manager
        
        # Initialize specialized agents
        self.doc_loader = DocumentLoaderAgent(vector_store)
        self.qa_agent = QAAgent(vector_store, session_manager)
        self.extraction_agent = ExtractionAgent()
        # self.report_agent = ReportAssemblyAgent(self.extraction_agent)
        self.report_agent = ReportAssemblyAgent()
        self.summarization_agent = SummarizationAgent()
        
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3)
        
        logger.info("Orchestrator initialized with Gemini Flash and all agents")
    
    async def process_documents(self, session_id: str, file_paths: List[str]) -> str:
        """Process uploaded documents through Document Loader Agent"""
        try:
            logger.info(f"Processing {len(file_paths)} documents for session {session_id}")
            result = await self.doc_loader.load_and_process(session_id, file_paths)
            self.session_manager.create_session(session_id, file_paths)
            logger.info(f"Documents processed successfully for session {session_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in document processing: {str(e)}")
            raise
    
    async def process_query(self, session_id: str, query: str) -> Dict:
        """Process user query through appropriate agent"""
        try:
            logger.info(f"Processing query for session {session_id}: {query}")
            
            # Classify intent
            intent = self._classify_intent(query)
            logger.info(f"Classified intent: {intent}")
            
            if intent == "qa":
                response = await self.qa_agent.answer_question(session_id, query)
            elif intent == "extraction":
                response = await self._handle_extraction(session_id, query)
            else:
                response = await self.qa_agent.answer_question(session_id, query)
            
            # Update conversation history
            self.session_manager.add_to_history(session_id, "user", query)
            self.session_manager.add_to_history(session_id, "assistant", response["answer"])
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise
    
    async def generate_report(self, session_id: str, sections: List[str]) -> str:
        """Generate structured report"""
        try:
            logger.info(f"Generating report for session {session_id}")
            session_data = self.session_manager.get_session(session_id)
            file_paths = session_data.get("file_paths", [])
            
            extracted_content = {}
            for section in sections:
                if section == "Summary":
                    summary = await self.summarization_agent.generate_summary(session_id, self.vector_store)
                    extracted_content[section] = summary
                else:
                    content = await self.extraction_agent.extract_for_section(file_paths, section)
                    extracted_content[section] = content
            
            report_path = await self.report_agent.assemble_report(session_id, extracted_content, sections)
            logger.info(f"Report generated successfully: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise
    
    def _classify_intent(self, query: str) -> str:
        """Classify user intent using Gemini Flash-2.5"""
        prompt = ChatPromptTemplate.from_template(
            """Classify the following query into one of these categories:
            - qa: General question answering about the documents
            - extraction: Specific request to extract tables, data, or images
            - report: Request to generate a report
            
            Query: {query}
            
            Respond with only the category name."""
        )
        
        try:
            messages = prompt.format_messages(query=query)
            response = self.llm.invoke(messages)
            intent = response.content.strip().lower()
            
            if intent not in ["qa", "extraction", "report"]:
                intent = "qa"
            return intent
            
        except Exception as e:
            logger.warning(f"Error classifying intent, defaulting to qa: {str(e)}")
            return "qa"
    
    async def _handle_extraction(self, session_id: str, query: str) -> Dict:
        """Handle extraction requests"""
        session_data = self.session_manager.get_session(session_id)
        file_paths = session_data.get("file_paths", [])
        extracted = await self.extraction_agent.extract_from_query(file_paths, query)
        
        return {
            "answer": extracted.get("content", "No data found."),
            "sources": extracted.get("sources", [])
        }
