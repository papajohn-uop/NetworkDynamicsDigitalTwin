# lets do analysis of the results
# automatic analuysis creation seems to work
# manual programmin will allow us to better understand flows and results




from baseline import baseline_analysis


 
    
  
def main():
    """
    Main driver script for manual experiments analysis.
    Executes the baseline analysis workflow across payload sizes
    and generates output statistical summary tables.
    """
    baseline_analysis()


if __name__ == "__main__":
    main()