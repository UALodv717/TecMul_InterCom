import math
import subprocess
import logging
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.axes as ax

class Processing:
    def __init__(self):
        self.quant = ["1", "2", "4", "8", "16", "32", "64", "128", "256", "512", "1024", "2048", "4096", "8182"]
        self.wavelets = ["db1", "db2", "db3", "db4", "db5", "sym4","sym5","bior3.3","bior3.5"]
        self.levels = ["1", "2", "3", "4", "5", "6", "7", "8","9","10"]

    def call_temporal_script_no_overlapping_16(self, quant, wavelet, level):
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
            result =subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
            # Process the captured standard output
                logging.info(f"Script output:\n{result.stdout}")
                return result.stdout
            else:
            # Log and process errors if the script failed
                logging.error(f"Script failed with error:\n{result.stderr}")
                return None
        except Exception as e:
            logging.error(f"An error occurred: {e}")

    def call_temporal_script_no_overlapping_32(self, quant, wavelet, level):
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
            result =subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
            # Process the captured standard output
                logging.info(f"Script output:\n{result.stdout}")
                return result.stdout
            else:
            # Log and process errors if the script failed
                logging.error(f"Script failed with error:\n{result.stderr}")
                return None

        except Exception as e:
            logging.error(f"An error occurred: {e}")

    def call_temporal_script_overlapping(self, quant, wavelet, level):
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
            result =subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
            # Process the captured standard output
                logging.info(f"Script output:\n{result.stdout}")
                return result.stdout
            else:
            # Log and process errors if the script failed
                logging.error(f"Script failed with error:\n{result.stderr}")
                return None
        except Exception as e:
            logging.error(f"An error occurred: {e}")

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
    
    for wavelet in processor.wavelets:
        for level in processor.levels:
            max_level = max_levels_per_wavelet.get(wavelet, 2)  # Default to 2 if undefined
            points = []  # Initialize points once per wavelet and level
        
            if int(level) > max_level:
                continue
        
            if (wavelet in ["sym4", "sym5", "bior3.3", "bior3.5"]) and (int(level) < 4 or int(level) > 5):
                continue
        
            logging.info(f"Processing wavelet={wavelet}, level={level}")
        
            for quant in processor.quant:
                logging.info(f"Processing quant={quant}, wavelet={wavelet}, level={level}")
            
                if sol == "n":
                    if type_no_overlapping == 16:
                        output = processor.call_temporal_script_no_overlapping_16(quant, wavelet, level)
                    else:
                        output = processor.call_temporal_script_no_overlapping_32(quant, wavelet, level)
                else:
                    output = processor.call_temporal_script_overlapping(quant, wavelet, level)
            
                if output:
                    lines = output.splitlines()
                    payload_sent_average = None
                    average_rmse = None
                
                    for line in lines:
                        if "Payload sent average " in line:
                            payload_sent_average = float(line.split("=")[1].strip().split()[0])
                        elif "Average RMSE (Root Mean Square Error) per sample " in line:
                            # Extract the part of the line containing the numbers
                            numbers_str = line.split("=")[1].strip().strip("[]")
                            # Split the numbers into a list of floats
                            numbers = [float(num) for num in numbers_str.split()]
                            # Calculate the average
                            average_rmse = sum(numbers) / len(numbers) if numbers else None
                
                    # Append the point only if both values are available
                    if payload_sent_average is not None and average_rmse is not None:
                        logging.info(f"KBPS: {payload_sent_average}, RMSE: {average_rmse}")
                        points.append((payload_sent_average, average_rmse))
                    else:
                        logging.warning(f"Missing data for quant={quant}. Skipping this point.")
        
            # Plot the RD curve for the current wavelet and level
            if points:
                points = sorted(points)  # Optional: Sort points by payload for better visualization
                plt.figure()
                plt.title(f"RD Tradeoff (Wavelet: {wavelet}, Level: {level})")
                plt.xlabel("R (Estimated Bits per Sample) [Entropy]")
                plt.ylabel("D (Root Mean Square Error)")
                plt.plot(*zip(*points), marker="o", linestyle="-", color="b", label=f"{wavelet}, Level {level}")
                plt.legend()
                plt.grid(True)
                plt.show()
