import subprocess
import os

def utility(input_path, output_path):
    try:
        print(f"Converting {input_path} to {output_path}")
        subprocess.run(
            [
                'soffice',
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', os.path.dirname(output_path),
                input_path
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        if not os.path.exists(output_path):
            raise RuntimeError(f"Conversion failed: Output file not found at {output_path}")
        
        print(f"File successfully converted to {output_path}")
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode('utf-8')
        raise RuntimeError(f"Conversion failed: {error_message}")
