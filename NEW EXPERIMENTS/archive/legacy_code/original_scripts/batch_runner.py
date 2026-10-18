import json
import subprocess
import time
import os

def run_batch():
    # Load experiment criteria Matrix
    if not os.path.exists('config.json'):
        print("❌ Error: config.json file missing.")
        return
        
    with open('config.json', 'r') as f:
        config = json.load(f)
        
    g_settings = config["global_settings"]
    iterations = g_settings["iterations_per_config"]
    cooldown = g_settings["cooldown_seconds"]
    core_script = g_settings["core_script_path"]
    
    print(f"🚀 Starting Automated Link Migration Sweep Loop...")
    print(f"🔄 Profile: {iterations} iterations per target with a {cooldown}s cool-down loop.")
    
    os.makedirs("results", exist_ok=True)
    
    # ============================================================
    # 0. PROCESSING PURE BASELINE CONTROL (Fixed & Explicitly Called)
    # ============================================================
    if "baseline_control" in config:
        print("\n📏 Launching Pure Baseline Control Group...")
        for b_name, params in config["baseline_control"].items():
            rate = params["rate"]
            lat = params["latency"]
            jit = params["jitter"]
            loss = params["loss"]
            out_name = params["output_name"]
            
            for i in range(1, iterations + 1):
                print(f"   ➔ Control Group [{b_name}] | Iteration {i}/{iterations}...")
                # Call core execution script: syntax holds blanks safely for baseline
                subprocess.run(["sudo", core_script, rate, lat, jit, loss, out_name], check=True)
                time.sleep(cooldown)


    # 1. Processing Parametric Sweeps
    for sweep_name, params in config["parametric_sweeps"].items():
        print(f"\n📈 Launching Sweep Strategy: {sweep_name}")
        rate = params["rate"]
        
        if sweep_name == "latency_sweep":
            var_list = [(v, params["jitter"], params["loss"]) for v in params["latency_values"]]
        elif sweep_name == "loss_sweep":
            var_list = [(params["latency"], params["jitter"], v) for v in params["loss_values"]]
        elif sweep_name == "jitter_sweep":
            var_list = [(params["latency"], v, params["loss"]) for v in params["jitter_values"]]
            
        for lat, jit, loss in var_list:
            profile_name = f"sweep_{sweep_name}_{lat}_{jit}_{loss}".replace('%','').replace('.','')
            for i in range(1, iterations + 1):
                print(f"   ➔ Iteration {i}/{iterations} for Config [Rate: {rate} | Latency: {lat} | Jitter: {jit} | Loss: {loss}]")
                subprocess.run(["sudo", core_script, rate, lat, jit, loss, profile_name], check=True)
                time.sleep(cooldown)

    # 2. Processing Scenario Profiles
    print("\n🎬 Launching Scenario Profile Evaluator...")
    for scenario in config["scenario_profiles"]:
        name = scenario["name"]
        rate = scenario["rate"]
        lat = scenario["latency"]
        jit = scenario["jitter"]
        loss = scenario["loss"]
        
        for i in range(1, iterations + 1):
            print(f"   ➔ Scenario {name} | Iteration {i}/{iterations}...")
            subprocess.run(["sudo", core_script, rate, lat, jit, loss, name], check=True)
            time.sleep(cooldown)
            
    print("\n✅ Structural Matrix Testing Suite Completed successfully!")

if __name__ == '__main__':
    run_batch()