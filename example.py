import streamlit.components.v1 as components
import base64

def mermaid(code: str) -> None:
    components.html(
        f"""
        <div id="mermaid-container" class="mermaid">
            {code}
        </div>

        <button id="download-btn">Download SVG</button>

        <script type="module">
            // Import Mermaid library from CDN
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            // Initialize Mermaid with specified options
            mermaid.initialize({{ startOnLoad: true ,securityLevel: 'loose',}});
            
            // Event listener for download button click
            document.getElementById('download-btn').onclick = function() {{
                // Extract SVG content from container
                const svgContent = document.getElementById('mermaid-container').innerHTML;
                // Create Blob from SVG content
                const svgBlob = new Blob([svgContent], {{ type: 'image/svg+xml' }});
                // Generate URL for Blob object
                const svgUrl = URL.createObjectURL(svgBlob);
                // Create a download link
                const downloadLink = document.createElement('a');
                downloadLink.href = svgUrl;  // Set download link href
                downloadLink.download = 'diagram.svg';  // Set download file name
                // Append download link to body
                document.body.appendChild(downloadLink);
                // Simulate click on download link
                downloadLink.click();
                // Remove download link from body
                document.body.removeChild(downloadLink);
            }};
        </script>
        """,
        height=600  # Default height for the Mermaid diagram
    )

mermaid(
    """
    sequenceDiagram
    Alice ->> Bob: Hello Bob, how are you?
    Bob-->>John: How about you John?
    Bob--x Alice: I am good thanks!
    Bob-x John: I am good thanks!
    Note right of John: Bob thinks a long<br/>long time, so long<br/>that the text does<br/>not fit on a row.

    Bob-->Alice: Checking with John...
    Alice->John: Yes... John, how are you?
    """
)
