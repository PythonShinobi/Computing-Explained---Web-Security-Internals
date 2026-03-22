import json
import pandas as pd

filename = "json/raft_small_file/ffuf_results_user_info_raft_small_files_filtered.json"

# -----------------------------
# CONFIG
# -----------------------------
def setup_display():
    """
    Configure pandas display options for better readability of DataFrames.

    This function sets pandas options to:
    - Show all rows and columns
    - Display full content of each cell without truncation
    - Adjust the display width automatically

    Useful when inspecting large DataFrames from ffuf results or
    other datasets in the console.

    Args:
        None

    Returns:
        None
    """

    # Show all rows when printing a DataFrame (no truncation)
    pd.set_option('display.max_rows', None)

    # Show all columns when printing a DataFrame (no truncation)
    pd.set_option('display.max_columns', None)

    # Show full content in each cell (do not truncate long strings)
    pd.set_option('display.max_colwidth', None)

    # Adjust display width automatically to fit the content
    pd.set_option('display.width', None)


# -----------------------------
# DATA LOADING
# -----------------------------
def load_data(file):
    """
    Load ffuf JSON results from a file and convert them into a pandas DataFrame.

    This function reads a JSON file containing ffuf results, extracts the
    "results" list, and returns it as a structured DataFrame for easier
    analysis.

    Args:
        file (str):
            Path to the JSON file containing ffuf results.

    Returns:
        pandas.DataFrame:
            A DataFrame where each row corresponds to a single ffuf result,
            including attributes such as 'url', 'status', 'length', 'words',
            'lines', and 'duration'.
    """

    # Open the JSON file for reading
    with open(file) as f:
        # Load the JSON content into a Python dictionary
        data = json.load(f)

    # Extract the "results" key and convert it into a pandas DataFrame
    return pd.DataFrame(data["results"])


# -----------------------------
# BASIC INSPECTION
# -----------------------------
def print_first_n_rows(df, rows=20):
    """
    Print the first n rows of a DataFrame.

    This function is useful for quickly inspecting the top entries
    of ffuf results or any DataFrame to get a sense of the data
    structure and content.

    Args:
        df (pandas.DataFrame):
            The DataFrame to inspect.

        rows (int, optional):
            The number of rows to print from the top of the DataFrame.
            Default is 20.

    Returns:
        None
            Prints the first n rows of the DataFrame to the console.
    """

    # Use pandas .head() method to get the first 'rows' entries
    # Then print them to the console
    print(df.head(rows))


# -----------------------------
# ANALYSIS
# -----------------------------
def analyze_uniques(df):
    """
    Print the counts of unique values for key response attributes
    in a DataFrame of ffuf results.

    This function helps identify which response characteristics vary
    and which are common, giving insight into baseline vs. anomalous
    responses. It is useful for quickly assessing the distribution
    of response lengths, word counts, line counts, and HTTP status codes.

    Args:
        df (pandas.DataFrame):
            DataFrame containing ffuf results. Must include columns:
            'length', 'words', 'lines', and 'status'.

    Returns:
        None
            Prints the value counts directly to the console.
    """

    # Print header for clarity
    print("\n=== UNIQUE VALUE COUNTS ===")

    # Loop over selected columns of interest
    for col in ["length", "words", "lines", "status"]:
        # Print the column name in uppercase for visibility
        print(f"\n{col.upper()}:")
        # Print the counts of each unique value in the column
        # value_counts() shows how many times each distinct value appears
        print(df[col].value_counts())

# -----------------------------
# BASELINE DETECTION
# -----------------------------
def get_baseline(df):
    """
    Determine the baseline (most common) response characteristics
    from a DataFrame of ffuf results.

    The baseline represents the "normal" or most frequently occurring
    response, typically corresponding to default pages or fallback behavior.
    It is used as a reference point for identifying anomalies.

    Args:
        df (pandas.DataFrame):
            DataFrame containing ffuf results. Must include the columns:
            'length', 'words', and 'lines'.

    Returns:
        dict:
            A dictionary containing the most common values for:
            - 'length': most frequent response size
            - 'words': most frequent word count
            - 'lines': most frequent line count
    """

    # Compute the mode (most frequent value) of the 'length' column
    # .mode() returns a Series; [0] selects the first (most common) value
    length_mode = df["length"].mode()[0]

    # Compute the mode (most frequent value) of the 'words' column
    words_mode = df["words"].mode()[0]

    # Compute the mode (most frequent value) of the 'lines' column
    lines_mode = df["lines"].mode()[0]

    # Return the baseline as a dictionary for easy access
    return {
        "length": length_mode,
        "words": words_mode,
        "lines": lines_mode,
    }

# -----------------------------
# FILTERING
# -----------------------------
def filter_outliers(df):
    """
    Filter out baseline (common) responses and return only outliers.

    This function identifies the most common response characteristics
    (length, words, lines) using the baseline, and removes all rows
    that match this baseline. The remaining rows represent responses
    that differ from the norm and are therefore more interesting
    for analysis.

    Args:
        df (pandas.DataFrame):
            DataFrame containing ffuf results. Must include 'length',
            'words', and 'lines' columns.

    Returns:
        pandas.DataFrame:
            A filtered DataFrame containing only rows that differ
            from the baseline in at least one of the measured attributes.
    """

    # Get the baseline values (most common length, words, and lines)
    # This represents the "normal" or default response
    baseline = get_baseline(df)

    # Print the baseline for visibility and debugging
    # Helps you understand what is being filtered out
    print("\n=== BASELINE ===")
    print(baseline)

    # Filter the DataFrame:
    # Keep rows where ANY of the following is true:
    # - length is different from baseline
    # - words count is different from baseline
    # - line count is different from baseline
    # The '|' operator means logical OR
    filtered = df[
        (df["length"] != baseline["length"]) |
        (df["words"] != baseline["words"]) |
        (df["lines"] != baseline["lines"])
    ]

    # Return only the outlier rows (non-baseline responses)
    return filtered


# -----------------------------
# SORTING
# -----------------------------
def sort_interesting(df):
    """
    Sort a DataFrame of filtered (interesting) ffuf results based on
    response characteristics.

    The sorting prioritizes larger responses and slower responses,
    which are often more meaningful during analysis:
    - Larger 'length' may indicate more content returned
    - Higher 'words' count may indicate richer or different responses
    - Longer 'duration' may suggest heavier processing or backend activity

    Args:
        df (pandas.DataFrame):
            DataFrame containing filtered ffuf results. Expected to include
            'length', 'words', and 'duration' columns.

    Returns:
        pandas.DataFrame:
            The sorted DataFrame, ordered by length, words, and duration
            in descending order (most interesting entries first).
    """

    # Sort the DataFrame based on multiple columns:
    # - 'length': prioritize larger response sizes
    # - 'words': prioritize responses with more content
    # - 'duration': prioritize slower responses (potentially more complex processing)
    # ascending=False means highest values appear first
    return df.sort_values(
        by=["length", "words", "duration"],
        ascending=False
    )


# -----------------------------
# RARE VALUE DETECTION
# -----------------------------
def get_files_with_unique_values(df):
    """
    Identify and return rows where response characteristics (length, words, or lines)
    are unique (i.e., occur exactly once in the dataset).

    This function is useful for detecting highly unusual or anomalous responses
    in ffuf results. Unique values often indicate endpoints that behave differently
    from the baseline and may reveal hidden functionality or errors.

    Args:
        df (pandas.DataFrame):
            DataFrame containing ffuf results. Must include the following columns:
            'url', 'status', 'length', 'words', 'lines', and 'duration'.

    Returns:
        pandas.DataFrame:
            A filtered DataFrame containing only rows where at least one of
            'length', 'words', or 'lines' is unique across the dataset.
            Only selected columns are returned for easier analysis.
    """

    # Find response sizes (length) that occur exactly once
    # value_counts() counts occurrences, and [lambda x: x == 1] filters counts == 1
    # .index extracts the actual length values that are unique
    rare_lengths = df["length"].value_counts()[lambda x: x == 1].index

    # Find word counts that occur exactly once
    rare_words = df["words"].value_counts()[lambda x: x == 1].index

    # Find line counts that occur exactly once
    rare_lines = df["lines"].value_counts()[lambda x: x == 1].index

    # Filter the DataFrame:
    # Keep rows where ANY of the following is true:
    # - length is unique
    # - words count is unique
    # - lines count is unique
    # The '|' operator means logical OR
    unique_df = df[
        (df["length"].isin(rare_lengths)) |
        (df["words"].isin(rare_words)) |
        (df["lines"].isin(rare_lines))
    ]

    # Return only relevant columns for easier inspection and analysis
    return unique_df[["url", "status", "length", "words", "lines", "duration"]]


# -----------------------------
# RARE SIZE (< THRESHOLD)
# -----------------------------
def get_rare_sizes(df, threshold=10):
    """
    Identify response sizes (length values) that occur less frequently
    than a specified threshold.

    This function helps detect uncommon response sizes in ffuf results,
    which may indicate interesting or non-standard server behavior.

    Args:
        df (pandas.DataFrame):
            DataFrame containing ffuf results. Must include a 'length' column.

        threshold (int, optional):
            The maximum number of occurrences for a size to be considered "rare".
            Default is 10 (i.e., sizes appearing fewer than 10 times are returned).

    Returns:
        pandas.Series:
            A Series where:
            - Index = rare response sizes (length values)
            - Values = count of how many times each size appears
    """

    # Count how many times each response size (length) appears
    # Example: {41431: 500, 1234: 2, 5678: 1}
    size_counts = df["length"].value_counts()

    # Filter and return only sizes that occur fewer times than the threshold
    # This isolates rare or uncommon response sizes
    return size_counts[size_counts < threshold]


def get_files_by_rare_sizes(df, threshold=10):
    """
    Identify and return entries whose response sizes (length) occur
    less frequently than a specified threshold.

    This helps highlight anomalous or uncommon responses in ffuf results,
    which are often more interesting than the baseline (repeated responses).

    Args:
        df (pandas.DataFrame):
            DataFrame containing ffuf results. Must include a 'length' column
            and other metadata such as 'url', 'status', etc.

        threshold (int, optional):
            The maximum number of occurrences for a size to be considered "rare".
            Default is 10 (i.e., sizes appearing fewer than 10 times are kept).

    Returns:
        pandas.DataFrame:
            A filtered DataFrame containing only rows with rare response sizes,
            including selected columns for analysis.
    """

    # Count how many times each response size (length) appears
    # Example: {41431: 500 times, 1234: 2 times, ...}
    size_counts = df["length"].value_counts()

    # Select sizes that appear fewer times than the threshold
    # This isolates uncommon (rare) response sizes
    rare_sizes = size_counts[size_counts < threshold].index

    # Filter the DataFrame to keep only rows whose length is in rare_sizes
    # This keeps only entries with uncommon response sizes
    filtered = df[df["length"].isin(rare_sizes)]

    # Return only relevant columns for easier inspection
    return filtered[["url", "status", "length", "words", "lines", "duration"]]


# -----------------------------
# OPTIONAL: KEYWORD FILTER
# -----------------------------
def filter_by_keywords(df, keywords=None):
    """
    Filter rows in a DataFrame where the 'url' column contains
    any of the specified keywords.

    This function is useful for quickly identifying potentially
    interesting endpoints (e.g., admin panels, login pages, upload
    handlers, configuration files) during fuzzing analysis.

    Args:
        df (pandas.DataFrame):
            The DataFrame containing ffuf results. Must include a 'url' column.

        keywords (list of str, optional):
            A list of keywords to search for within the 'url' column.
            If not provided, a default set of common sensitive keywords
            is used: ["login", "admin", "upload", "config"].

    Returns:
        pandas.DataFrame:
            A filtered DataFrame containing only rows where the 'url'
            contains at least one of the specified keywords.
    """

    # If no custom keywords are provided, use a default list
    if keywords is None:
        keywords = ["login", "admin", "upload", "config"]

    # Join the list of keywords into a single regex pattern using '|'
    # Example: ["login", "admin"] -> "login|admin"
    # This allows matching any of the keywords
    pattern = "|".join(keywords)

    # Use pandas string matching to filter rows:
    # - df["url"] selects the URL column
    # - .str.contains(pattern) checks if the URL contains any keyword
    # - na=False ensures missing values (NaN) are treated as False (not matched)
    # The result is a boolean mask used to filter the DataFrame
    return df[df["url"].str.contains(pattern, na=False)]


# -----------------------------
# MAIN WORKFLOW
# -----------------------------
if __name__ == "__main__":
    setup_display()

    df = load_data(filename)

    # 1. Inspect
    print_first_n_rows(df, rows=20)

    # 2. Understand baseline
    analyze_uniques(df)

    # 3. Remove noise
    interesting = filter_outliers(df)

    print("\n=== INTERESTING (OUTLIERS) ===")
    print(interesting[["url", "length", "words", "lines"]])

    # 4. Sort
    sorted_df = sort_interesting(interesting)

    print("\n=== SORTED INTERESTING ===")
    print(sorted_df.head(20))

    # 5. Rare values
    unique_files = get_files_with_unique_values(df)

    print("\n=== UNIQUE VALUE FILES ===")
    print(unique_files)

    # 6. Rare sizes (<10 occurrences)
    rare_sizes = get_rare_sizes(df, threshold=10)
    print("\n=== RARE SIZES (<10 occurrences) ===")
    print(rare_sizes)

    rare_files = get_files_by_rare_sizes(df, threshold=10)
    print("\n=== FILES WITH RARE SIZES (<10) ===")
    print(rare_files)

    # 7. Keyword hits
    keyword_hits = filter_by_keywords(df)

    print("\n=== KEYWORD MATCHES ===")
    print(keyword_hits[["url", "length"]])
