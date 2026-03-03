import json
from transformers import DataExtractor

def test_example_1():
    extractor = DataExtractor()
    input_data = [
        {
            "nodes": [
                {"id": "A", "description": "Information processing module A"},
                {"id": "B", "description": "Decision-making unit B"},
                {"id": "C", "description": "Output generator C"}
            ],
            "links": [
                {"source": "A", "target": "B", "description": "A supplies structured data to B."},
                {"source": "B", "target": "C", "description": "B instructs C to generate an output."}
            ]
        }
    ]
    result = extractor.transform_graph_data(json.dumps(input_data))
    print("SUCCESS: ", result)

if __name__ == "__main__":
    test_example_1()
