"""
Main entry point for RCA Agent
"""

import logging
from typing import Dict, Any
from src.input_layer.defect_parser import DefectParser
from src.processing_layer.agents.orchestrator import AgentOrchestrator
from src.output_layer.diagnosis_generator import DiagnosisGenerator
from src.utils.config import load_config
from src.utils.logger import setup_logger


class RCAAgent:
    """Main RCA Agent orchestrating the entire analysis pipeline"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the RCA Agent"""
        self.config = load_config(config_path)
        self.logger = setup_logger(__name__)
        
        # Initialize components
        self.defect_parser = DefectParser()
        self.orchestrator = AgentOrchestrator(self.config)
        self.diagnosis_generator = DiagnosisGenerator()
        
    def analyze_defect(self, defect_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to analyze a defect
        
        Args:
            defect_data: Dictionary containing defect information
            
        Returns:
            Dictionary containing diagnosis and recommendations
        """
        self.logger.info(f"Starting analysis for defect: {defect_data.get('id', 'unknown')}")
        
        # Step 1: Parse and validate input
        parsed_defect = self.defect_parser.parse(defect_data)
        
        # Step 2: Run AI agents for analysis
        analysis_results = self.orchestrator.analyze(parsed_defect)
        
        # Step 3: Generate diagnosis
        diagnosis = self.diagnosis_generator.generate(analysis_results)
        
        self.logger.info(f"Analysis completed with confidence: {diagnosis.get('confidence', 0)}")
        
        return diagnosis


def main():
    """Main execution function"""
    logger = logging.getLogger(__name__)
    logger.info("Starting RCA Agent...")
    
    # Initialize agent
    agent = RCAAgent()
    
    # Example defect data
    sample_defect = {
        "id": "BUG-12345",
        "description": "Application crashes when processing large datasets",
        "timestamp": "2026-07-09T10:30:00Z",
        "logs": [],
        "comments": []
    }
    
    # Run analysis
    result = agent.analyze_defect(sample_defect)
    
    print(f"\n{'='*50}")
    print("DIAGNOSIS RESULTS")
    print(f"{'='*50}")
    print(f"Root Cause: {result.get('root_cause', 'Unknown')}")
    print(f"Confidence: {result.get('confidence', 0):.2%}")
    print(f"Recommended Team: {result.get('assigned_team', 'N/A')}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
