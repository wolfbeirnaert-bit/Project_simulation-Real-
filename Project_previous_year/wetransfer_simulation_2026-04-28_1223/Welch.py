import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter

def read_obj_fn_from_file(filename="Output_Radiology.txt"):
    """
    Read obj_fn values from the simulation output file.
    
    Format expected: tab-separated columns with obj_fn in the one but last column (6th column).
    The file has a header row "Number\tObservation\t..." followed by data rows.
    """
    # Skip header rows until the data starts
    with open(filename, 'r') as f:
        lines = f.readlines()
        
    # Find the line with column headers
    header_idx = None
    for i, line in enumerate(lines):
        if "Number\tCycle Time\tRunning Avg Cycle Time\tUtilization\tRunning Avg Utilization\tObjective Function\tRunning Avg Objectif Function" in line:
            header_idx = i
            break
    
    if header_idx is None:
        raise ValueError("Could not find header row in file. Make sure your output file has the expected format.")
    
    # Parse data rows after header
    obj_fn_values = []
    job_numbers = []
    
    for line in lines[header_idx+1:]:
        if line.strip():  # Skip empty lines
            parts = line.strip().split('\t')
            if len(parts) >= 6:  # We expect at least 6 columns
                job_numbers.append(int(parts[0]))
                obj_fn_values.append(float(parts[5]))  # 6th column (index 5) is obj_fn
    
    if not obj_fn_values:
        raise ValueError("No obj_fn values found in the file. Check the file format.")
        
    print(f"Successfully read {len(obj_fn_values)} obj_fn values from {filename}")
    return np.array(job_numbers), np.array(obj_fn_values)

def calculate_moving_average(data, window_size):
    """
    Calculate moving average according to Welch's method.
    
    For t = 1,...,w:
        Y_t(w) = (sum from i=1 to 2t-1) of Y_i / (2t-1)
    
    For t = w+1,...,T-w:
        Y_t(w) = (sum from i=t-w to t+w) of Y_i / (2w+1)
    
    Args:
        data: Array of data values
        window_size: Window size w for moving average
        
    Returns:
        Array of moving averages
    """
    n = len(data)
    moving_avgs = np.zeros(n)
    
    # Calculate moving averages following Welch's algorithm as shown in the slides
    for t in range(n):
        if t < window_size:
            # For t = 1,...,w: Y_t(w) = (sum from i=1 to 2t-1) of Y_i / (2t-1)
            # Note: we're using 0-based indexing, so the formula adjusts slightly
            end_idx = min(2*t+1, n)  # Ensure we don't go beyond array bounds
            moving_avgs[t] = np.mean(data[:end_idx])
        else:
            # For t = w+1,...,T-w: Y_t(w) = (sum from i=t-w to t+w) of Y_i / (2w+1)
            start_idx = t - window_size
            end_idx = min(t + window_size + 1, n)  # +1 because slicing is exclusive of end
            moving_avgs[t] = np.mean(data[start_idx:end_idx])
    
    return moving_avgs

def detect_warmup_period(obj_fn_values, window_sizes=[30, 50, 100, 200, 500]):
    """
    Detect the warm-up period using Welch's method with multiple window sizes.
    
    Steps:
    1. Calculate moving averages with each specified window size
    2. Analyze if the plot is smooth by checking for flatness
    3. The warm-up period is the point where the moving average becomes flat
    
    Args:
        obj_fn_values: Array of objective function values
        window_sizes: List of window sizes w to evaluate
        
    Returns:
        List of detected warm-up period indices for each window size
        Results dictionary with moving averages for each window size
    """
    n = len(obj_fn_values)
    
    # The value T is the total length of the time series (all observations)
    # This is an important parameter as it determines how much data we have
    # for the warm-up analysis. In our case, T = n (number of jobs completed)
    T = n
    
    print(f"Time series length T = {T} observations")
    print(f"Using {len(window_sizes)} different window sizes: {window_sizes}")
    print("Note: According to Law (2007), window size w is typically ≈ [T/4]")
    print(f"For our data, [T/4] = {T//4}, which is close to our middle window size")
    
    # Store results for different window sizes
    window_results = []
    warmup_indices = []
    
    # Calculate moving averages and detect warm-up period for each window size
    for window_size in window_sizes:
        # Ensure window size isn't too large for our data
        if window_size >= T/2:
            print(f"Warning: Window size {window_size} is quite large relative to T={T}")
            print(f"This may affect the reliability of the warm-up detection")
        
        # Calculate moving average
        moving_avgs = calculate_moving_average(obj_fn_values, window_size)
        
        # Calculate first and second derivatives to analyze flatness
        # First derivative approximation
        first_deriv = np.gradient(moving_avgs)
        
        # Second derivative approximation
        second_deriv = np.gradient(first_deriv)
        
        # Apply some smoothing to the derivatives to reduce noise
        smoothed_first_deriv = savgol_filter(first_deriv, min(51, len(first_deriv)-1), 3)
        smoothed_second_deriv = savgol_filter(second_deriv, min(51, len(second_deriv)-1), 3)
        
        # Find where the smoothed derivatives are close to zero
        # For first derivative, we're looking for where the curve becomes flat
        # For second derivative, we're looking for where the curvature becomes near-zero
        first_deriv_flat = np.abs(smoothed_first_deriv) < 0.01 * np.std(obj_fn_values)
        second_deriv_flat = np.abs(smoothed_second_deriv) < 0.01 * np.std(obj_fn_values)
        
        # Find the first point where both derivatives are flat for a sustained period
        # (we require at least 5% of the data length to be flat)
        min_flat_length = max(int(0.05 * T), 10)
        
        # Use a rolling window to check for sustained flatness
        flat_count = 0
        warmup_idx = None
        
        for i in range(T):
            if first_deriv_flat[i] and second_deriv_flat[i]:
                flat_count += 1
                if flat_count >= min_flat_length and warmup_idx is None:
                    # We've found a sustained flat period
                    warmup_idx = max(0, i - min_flat_length)
                    break
            else:
                flat_count = 0
        
        # If we couldn't find a clear warm-up period, use change point detection
        if warmup_idx is None:
            # Use change-point detection as an alternative approach
            # Calculate cumulative mean differences
            cum_mean_diff = np.zeros(T)
            for i in range(1, T):
                cum_mean_diff[i] = abs(np.mean(moving_avgs[:i]) - np.mean(moving_avgs[i:]))
            
            # The index with maximum difference is a candidate for change point
            warmup_idx = np.argmax(cum_mean_diff)
            
            print(f"For window size w={window_size}, no clear flat region found.")
            print(f"Used change-point detection to estimate warm-up at index {warmup_idx}")
        else:
            print(f"For window size w={window_size}, found clear warm-up at index {warmup_idx}")
        
        # Store results
        window_results.append({
            'window_size': window_size,
            'moving_avgs': moving_avgs,
            'warmup_idx': warmup_idx
        })
        
        warmup_indices.append(warmup_idx)
    
    # Find the most consistent warm-up period estimate
    # We'll use the median value to reduce the impact of outliers
    consensus_warmup_idx = int(np.median(warmup_indices))
    
    return consensus_warmup_idx, window_results, warmup_indices

def plot_welch_method_results(job_numbers, obj_fn_values, consensus_warmup_idx, window_results, warmup_indices):
    """Plot the results of Welch's method for visual analysis"""
    # Get the specific window sizes
    window_sizes = [result['window_size'] for result in window_results]
    
    # Create a figure with multiple subplots
    # 1. Original data with consensus warm-up
    # 2. All moving averages on one plot
    # 3. Individual moving averages for each window size
    num_window_sizes = len(window_sizes)
    fig_height = 6 + 3 * num_window_sizes  # Base height + height per window size plot
    
    fig, axes = plt.subplots(2 + num_window_sizes, 1, figsize=(14, fig_height))
    
    # Determine T (number of observations)
    T = len(obj_fn_values)
    
    # Plot 1: Original obj_fn values with consensus warm-up period marked
    axes[0].plot(job_numbers, obj_fn_values, 'b-', alpha=0.5, label='Original obj_fn values')
    axes[0].axvline(x=job_numbers[consensus_warmup_idx], color='r', linestyle='--', 
                   label=f'Consensus warm-up period end: Job {job_numbers[consensus_warmup_idx]}')
    # Add annotation explaining T
    axes[0].annotate(f'T = {T} observations (total jobs processed)', 
                   xy=(0.5, 0.95), xycoords='axes fraction',
                   ha='center', va='top',
                   bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.3))
    axes[0].set_xlabel('Job Number')
    axes[0].set_ylabel('obj_fn Value')
    axes[0].set_title('Original obj_fn Values with Consensus Warm-up Period')
    axes[0].legend()
    axes[0].grid(True)
    
    # Plot 2: All moving averages on one plot with all warm-up periods marked
    colors = plt.cm.viridis(np.linspace(0, 1, num_window_sizes))
    
    for i, result in enumerate(window_results):
        w = result['window_size']
        warmup_idx = result['warmup_idx']
        color = colors[i]
        
        # Plot moving average
        axes[1].plot(job_numbers, result['moving_avgs'], color=color, 
                    label=f'w={w}')
        
        # Mark warm-up point
        axes[1].axvline(x=job_numbers[warmup_idx], color=color, linestyle='--',
                       alpha=0.7)
    
    # Mark consensus warm-up
    axes[1].axvline(x=job_numbers[consensus_warmup_idx], color='r', linestyle='-', 
                   label=f'Consensus warm-up: Job {job_numbers[consensus_warmup_idx]}')
    
    # Add annotation about recommended window size
    recommended_w = T // 4
    axes[1].annotate(f'Recommended w ≈ [T/4] = {recommended_w}\nper Law (2007)', 
                   xy=(0.02, 0.95), xycoords='axes fraction',
                   ha='left', va='top',
                   bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.3))
    
    axes[1].set_xlabel('Job Number')
    axes[1].set_ylabel('Moving Average Y_t(w)')
    axes[1].set_title('Comparison of All Moving Averages (Different Window Sizes)')
    axes[1].legend(loc='upper right')
    axes[1].grid(True)
    
    # Individual plots for each window size
    for i, result in enumerate(window_results):
        w = result['window_size']
        warmup_idx = result['warmup_idx']
        ax_idx = i + 2  # Start at index 2 for individual plots
        
        axes[ax_idx].plot(job_numbers, result['moving_avgs'], color=colors[i], 
                         label=f'Moving average (w={w})')
        axes[ax_idx].axvline(x=job_numbers[warmup_idx], color='r', linestyle='--',
                            label=f'Warm-up end: Job {job_numbers[warmup_idx]}')
        
        # Add visual elements to show the window size
        # Show a horizontal bar representing the window size
        bar_y = np.min(obj_fn_values) - 0.1 * (np.max(obj_fn_values) - np.min(obj_fn_values))
        middle_x = T // 2
        
        # Get appropriate y position for the window size indicator
        y_min, y_max = axes[ax_idx].get_ylim()
        bar_y = y_min - 0.1 * (y_max - y_min)
        
        # Add window size annotation
        if 2*w < T:  # Only show if window fits on the plot
            axes[ax_idx].annotate(f'Window size w={w}', 
                               xy=(middle_x, bar_y),
                               xytext=(0, -20), textcoords='offset points',
                               ha='center', va='top',
                               bbox=dict(boxstyle="round,pad=0.3", fc="lightblue", alpha=0.3))
        
        axes[ax_idx].set_xlabel('Job Number')
        axes[ax_idx].set_ylabel('Moving Average Y_t(w)')
        axes[ax_idx].set_title(f'Moving Average with Window Size w={w}')
        axes[ax_idx].legend(loc='upper right')
        axes[ax_idx].grid(True)
    
    plt.tight_layout()
    plt.savefig('welch_warmup_analysis.png')
    
    # Also create a focused plot around the warm-up period
    plt.figure(figsize=(14, 8))
    
    # Select a range around the consensus warm-up period for better visibility
    focus_start = max(0, consensus_warmup_idx - 500)
    focus_end = min(len(job_numbers), consensus_warmup_idx + 500)
    
    # Plot original data
    plt.plot(job_numbers[focus_start:focus_end], 
             obj_fn_values[focus_start:focus_end], 'b-', alpha=0.3, label='Original obj_fn values')
    
    # Plot all moving averages in the focus area
    for i, result in enumerate(window_results):
        w = result['window_size']
        warmup_idx = result['warmup_idx']
        color = colors[i]
        
        # Plot moving average in focus area
        plt.plot(job_numbers[focus_start:focus_end], 
                result['moving_avgs'][focus_start:focus_end], 
                color=color, label=f'Moving avg (w={w})')
        
        # Mark this window's warm-up point if it's in the focus area
        if focus_start <= warmup_idx <= focus_end:
            plt.axvline(x=job_numbers[warmup_idx], color=color, linestyle='--',
                       alpha=0.7, label=f'Warm-up for w={w}: Job {job_numbers[warmup_idx]}')
    
    # Mark consensus warm-up
    plt.axvline(x=job_numbers[consensus_warmup_idx], color='r', linestyle='-', linewidth=2,
               label=f'Consensus warm-up: Job {job_numbers[consensus_warmup_idx]}')
    
    plt.xlabel('Job Number')
    plt.ylabel('Value')
    plt.title('Detailed View Around Consensus Warm-up Period')
    plt.legend(loc='best')
    plt.grid(True)
    
    plt.savefig('welch_warmup_detailed.png')

def calculate_statistics_after_warmup(obj_fn_values, warmup_idx):
    """Calculate statistics for obj_fn after warm-up period"""
    # Use only data after warm-up period
    steady_state_data = obj_fn_values[warmup_idx:]
    
    mean = np.mean(steady_state_data)
    std_dev = np.std(steady_state_data)
    variance = np.var(steady_state_data)
    min_val = np.min(steady_state_data)
    max_val = np.max(steady_state_data)
    
    # Calculate 95% confidence interval
    n = len(steady_state_data)
    ci_half_width = 1.96 * std_dev / np.sqrt(n)
    ci_lower = mean - ci_half_width
    ci_upper = mean + ci_half_width
    
    return {
        'mean': mean,
        'std_dev': std_dev,
        'variance': variance,
        'min': min_val,
        'max': max_val,
        'n': n,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper
    }

def main():
    try:
        # Read obj_fn values from simulation output
        job_numbers, obj_fn_values = read_obj_fn_from_file()
        
        # Define the window sizes to test based on requirements
        window_sizes = [30, 50, 100, 200, 500]
        
        # T = length of time series (all observations)
        # In our case, T = number of jobs completed in the simulation
        T = len(obj_fn_values)
        
        print(f"\nAnalyzing warm-up period using Welch's method (1981)")
        print(f"Time series length T = {T} observations")
        print(f"Window sizes to test: {window_sizes}")
        print(f"Law (2007) recommends window size w ≈ [T/4] = {T//4}")
        
        # Explanation of T choice
        print("\nJustification for time series length T:")
        print(f"1. T = {T} represents the total number of jobs processed in the simulation")
        print("2. Using the full dataset provides maximum information for warm-up detection")
        print("3. The simulation was designed to run until steady state is achieved")
        print("4. This approach aligns with the Welch method which analyzes the entire time series")
        print("5. A shorter T might miss the true warm-up period if transient effects last longer")
        
        # Detect warm-up period using Welch's method with all window sizes
        consensus_warmup_idx, window_results, warmup_indices = detect_warmup_period(obj_fn_values, window_sizes)
        
        print("\nWarm-up period detection results:")
        print("-" * 60)
        print(f"{'Window Size (w)':<15} {'Job Number':<15} {'% of Total Jobs':<20}")
        print("-" * 60)
        
        for i, w in enumerate(window_sizes):
            warmup_idx = warmup_indices[i]
            job_num = job_numbers[warmup_idx]
            percent = (warmup_idx / T) * 100
            print(f"{w:<15} {job_num:<15} {percent:.2f}%")
        
        print("-" * 60)
        print(f"Consensus warm-up: {job_numbers[consensus_warmup_idx]} (median of all estimates)")
        print(f"This means data before job {job_numbers[consensus_warmup_idx]} should be discarded for steady-state analysis.")
        
        # Plot results
        plot_welch_method_results(job_numbers, obj_fn_values, consensus_warmup_idx, window_results, warmup_indices)
        
        # Calculate statistics after warm-up
        stats = calculate_statistics_after_warmup(obj_fn_values, consensus_warmup_idx)
        
        print("\nStatistics for obj_fn after warm-up period:")
        print(f"Mean: {stats['mean']:.6f}")
        print(f"Standard Deviation: {stats['std_dev']:.6f}")
        print(f"Variance: {stats['variance']:.6f}")
        print(f"Minimum: {stats['min']:.6f}")
        print(f"Maximum: {stats['max']:.6f}")
        print(f"Number of observations (after warm-up): {stats['n']} ({stats['n']/T:.1%} of total)")
        print(f"95% Confidence Interval: ({stats['ci_lower']:.6f}, {stats['ci_upper']:.6f})")
        
        # Save warm-up detection results to file
        with open('warmup_results.txt', 'w') as f:
            f.write("Warm-up Period Analysis using Welch's Method (1981)\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Time series length T = {T} observations\n")
            f.write(f"Recommended window size per Law (2007): w ≈ [T/4] = {T//4}\n\n")
            
            f.write("Results for different window sizes:\n")
            f.write("-" * 60 + "\n")
            f.write(f"{'Window Size (w)':<15} {'Job Number':<15} {'% of Total Jobs':<20}\n")
            f.write("-" * 60 + "\n")
            
            for i, w in enumerate(window_sizes):
                warmup_idx = warmup_indices[i]
                job_num = job_numbers[warmup_idx]
                percent = (warmup_idx / T) * 100
                f.write(f"{w:<15} {job_num:<15} {percent:.2f}%\n")
            
            f.write("-" * 60 + "\n")
            f.write(f"Consensus warm-up period ends at job number: {job_numbers[consensus_warmup_idx]}\n")
            f.write(f"(This is the median of all estimates)\n\n")
            
            f.write("Statistics for obj_fn after warm-up period:\n")
            f.write(f"Mean: {stats['mean']:.6f}\n")
            f.write(f"Standard Deviation: {stats['std_dev']:.6f}\n")
            f.write(f"Variance: {stats['variance']:.6f}\n")
            f.write(f"Minimum: {stats['min']:.6f}\n")
            f.write(f"Maximum: {stats['max']:.6f}\n")
            f.write(f"Number of observations (after warm-up): {stats['n']} ({stats['n']/T:.1%} of total)\n")
            f.write(f"95% Confidence Interval: ({stats['ci_lower']:.6f}, {stats['ci_upper']:.6f})\n\n")
            
            f.write("Justification for time series length T:\n")
            f.write("1. T represents the total number of jobs processed in the simulation\n")
            f.write("2. Using the full dataset provides maximum information for warm-up detection\n")
            f.write("3. The simulation was designed to run until steady state is achieved\n")
            f.write("4. This approach aligns with the Welch method which analyzes the entire time series\n")
            f.write("5. A shorter T might miss the true warm-up period if transient effects last longer\n")
        
        print(f"\nResults saved to 'warmup_results.txt'")
        print(f"Plots saved as 'welch_warmup_analysis.png' and 'welch_warmup_detailed.png'")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Please make sure the simulation output file exists and has the expected format.")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()