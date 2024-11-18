import subprocess
import logging
import os
import sys

class Processing:
    def __init__(self):
        self.quant = ["1", "2", "4", "8", "16", "32", "64", "128", "256", "512", "1024", "2048", "4096", "8182"]
        self.wavelets = ["db1", "db2", "db3", "db4", "db5"]
        self.levels = ["1", "2", "3", "4", "5", "6", "7", "8","9","10"]
    
    def call_temporal_script_no_overlapping_16(self, quant, wavelet, level, output_file):
        """
        Calls the 'temporal_no_overlapped_DWT_coding_16.py' script using subprocess,
        and saves the output to a specified file.

        :param quant: Quantization value (string).
        :param wavelet: Wavelet type (string).
        :param level: Level value (string).
        :param output_file: Path to the output text file.
        """
        starting_path= os.getcwd()
        script_path=os.path.join(starting_path, "src", "temporal_no_overlapped_DWT_coding_16.py")
        executorpy=sys.executable
        filesong=os.path.join(starting_path, "data", "AviadorDro_LaZonaFantasma.oga")
        try:
            # Command to execute the script with parameters
            cmd = [
                executorpy, 
                script_path,
                "-q", quant,
                "-w", wavelet,
                "-e", level,
                "--show_stats",
                "-f", filesong,
                "-t","20"
            ]

            # Logging the command being executed for debugging
            logging.info(f"Executing command: {' '.join(cmd)}")

            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True)

            # Write the output to the file
            with open(output_file, "w") as f:
                f.write(f"Command: {' '.join(cmd)}\n")
                if result.returncode == 0:
                    f.write("Script executed successfully.\n")
                    f.write("Output:\n")
                    f.write(result.stdout)
                else:
                    f.write("Script execution failed.\n")
                    f.write("Error:\n")
                    f.write(result.stderr)

            # Log the result
            if result.returncode == 0:
                logging.info("Script executed successfully. Output saved to file.")
            else:
                logging.error("Script execution failed. Error saved to file.")

        except Exception as e:
            logging.error(f"An error occurred: {e}")

    def call_temporal_script_no_overlapping_32(self, quant, wavelet, level, output_file):
        """
        Calls the 'temporal_no_overlapped_DWT_coding_32.py' script using subprocess,
        and saves the output to a specified file.

        :param quant: Quantization value (string).
        :param wavelet: Wavelet type (string).
        :param level: Level value (string).
        :param output_file: Path to the output text file.
        """
        starting_path= os.getcwd()
        script_path=os.path.join(starting_path, "src", "temporal_no_overlapped_DWT_coding_32.py")
        executorpy=sys.executable
        filesong=os.path.join(starting_path, "data", "AviadorDro_LaZonaFantasma.oga")
        try:
            # Command to execute the script with parameters
            cmd = [
                executorpy, 
                script_path,
                "-q", quant,
                "-w", wavelet,
                "-e", level,
                "--show_stats",
                "-f", filesong,
                "-t","20"
            ]

            # Logging the command being executed for debugging
            logging.info(f"Executing command: {' '.join(cmd)}")

            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True)

            # Write the output to the file
            with open(output_file, "w") as f:
                f.write(f"Command: {' '.join(cmd)}\n")
                if result.returncode == 0:
                    f.write("Script executed successfully.\n")
                    f.write("Output:\n")
                    f.write(result.stdout)
                else:
                    f.write("Script execution failed.\n")
                    f.write("Error:\n")
                    f.write(result.stderr)

            # Log the result
            if result.returncode == 0:
                logging.info("Script executed successfully. Output saved to file.")
            else:
                logging.error("Script execution failed. Error saved to file.")

        except Exception as e:
            logging.error(f"An error occurred: {e}")

    def call_temporal_script_overlapping(self, quant, wavelet, level, output_file):
        """
        Calls the 'temporal_overlapped_DWT_coding.py' script using subprocess,
        and saves the output to a specified file.

        :param quant: Quantization value (string).
        :param wavelet: Wavelet type (string).
        :param level: Level value (string).
        :param output_file: Path to the output text file.
        """
        starting_path= os.getcwd()
        script_path=os.path.join(starting_path, "src", "temporal_overlapped_DWT_coding.py")
        executorpy=executorpy=sys.executable
        filesong=os.path.join(starting_path, "data", "AviadorDro_LaZonaFantasma.oga")
        try:
            # Command to execute the script with parameters
            cmd = [
                executorpy, 
                script_path,
                "-q", quant,
                "-w", wavelet,
                "-e", level,
                "--show_stats",
                "-f", filesong,
                "-t","20"
            ]

            # Logging the command being executed for debugging
            logging.info(f"Executing command: {' '.join(cmd)}")

            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True)

            # Write the output to the file
            with open(output_file, "w") as f:
                f.write(f"Command: {' '.join(cmd)}\n")
                if result.returncode == 0:
                    f.write("Script executed successfully.\n")
                    f.write("Output:\n")
                    f.write(result.stdout)
                else:
                    f.write("Script execution failed.\n")
                    f.write("Error:\n")
                    f.write(result.stderr)

            # Log the result
            if result.returncode == 0:
                logging.info("Script executed successfully. Output saved to file.")
            else:
                logging.error("Script execution failed. Error saved to file.")

        except Exception as e:
            logging.error(f"An error occurred: {e}")

# Example usage:
if __name__ == "__main__":
    
    logging.basicConfig(level=logging.INFO)
    sol=input("Do you want to overlap the signals? (y/n) ").lower()
    absolute_path=os.getcwd()
    
    if(sol=="n"):
        user_input = input("Do you want to use MST_16 or MST_32 for no overlap (16/32)? (Default is 16): ")
        type_no_overlapping = int(user_input) if user_input.strip() else 16
    
    # Initialize the processor
    processor = Processing()

    # Path to the output log directory
    if(sol=="n"):
        if(type_no_overlapping==16):
            output_dir=os.path.join(absolute_path, "docs", "log_no_overlapped_16")
        else:
            output_dir=os.path.join(absolute_path, "docs", "log_no_overlapped_32")
    else:
        output_dir=os.path.join(absolute_path, "docs", "log_overlapped")
    os.makedirs(output_dir, exist_ok=True)

    # Define maximum levels for each wavelet type
    if(sol=="n"):
        max_levels_per_wavelet = {
            "db1": 10,
            "db2": 10,
            "db3": 10,
            "db4": 10,
            "db5": 10,
        }
    else:
        max_levels_per_wavelet = {
            "db1": 9,
            "db2": 8,
            "db3": 7,
            "db4": 7,
            "db5": 6,
        }

    # Iterate through combinations with constraint on levels
    for quant in processor.quant:
        for wavelet in processor.wavelets:
            max_level = max_levels_per_wavelet.get(wavelet, 2)  # Default to 2 if undefined
            for level in processor.levels:
                if int(level) > max_level:
                    continue 
                
                output_file = os.path.join(
                    output_dir, f"output_w{wavelet}_l{level}_q{quant}.txt"
                )
                
                logging.info(f"Processing quant={quant}, wavelet={wavelet}, level={level}")
                
                if(sol=="n"):
                    if(type_no_overlapping==16):
                        processor.call_temporal_script_no_overlapping_16(quant, wavelet, level, output_file)
                    else:
                        processor.call_temporal_script_no_overlapping_32(quant, wavelet, level, output_file)
                else:
                    processor.call_temporal_script_overlapping(quant, wavelet, level, output_file)
