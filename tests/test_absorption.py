import json

import torch

import evals.absorption.eval_config as eval_config
import evals.absorption.main as absorption
import sae_bench_utils.formatting_utils as formatting_utils
import sae_bench_utils.testing_utils as testing_utils

results_filename = "tests/test_data/absorption_expected_results.json"


def test_end_to_end_different_seed():
    """Estimated runtime: 2 minutes"""
    if torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Using device: {device}")

    test_config = eval_config.EvalConfig()
    test_config.sae_releases = [
        "sae_bench_pythia70m_sweep_topk_ctx128_0730",
    ]

    test_config.model_name = "pythia-70m-deduped"
    test_config.layer = 4
    test_config.trainer_ids = [10]
    test_config.include_checkpoints = False
    test_config.random_seed = 44
    tolerance = 0.02

    # populate selected_saes_dict using config values
    for release in test_config.sae_releases:
        if "gemma-scope" in release:
            test_config.selected_saes_dict[release] = (
                formatting_utils.find_gemmascope_average_l0_sae_names(test_config.layer)
            )
        else:
            test_config.selected_saes_dict[release] = formatting_utils.filter_sae_names(
                sae_names=release,
                layers=[test_config.layer],
                include_checkpoints=test_config.include_checkpoints,
                trainer_ids=test_config.trainer_ids,
            )

        print(f"SAE release: {release}, SAEs: {test_config.selected_saes_dict[release]}")

    run_results = absorption.run_eval(test_config, test_config.selected_saes_dict, device)

    # with open(results_filename, "w") as f:
    #     json.dump(run_results, f)

    with open(results_filename, "r") as f:
        expected_results = json.load(f)

    expected_mean_absorption_rate = expected_results["custom_eval_results"][
        "pythia70m_sweep_topk_ctx128_0730/resid_post_layer_4/trainer_10"
    ]["mean_absorption_rate"]

    actual_mean_absorption_rate = run_results["custom_eval_results"][
        "pythia70m_sweep_topk_ctx128_0730/resid_post_layer_4/trainer_10"
    ]["mean_absorption_rate"]

    assert abs(actual_mean_absorption_rate - expected_mean_absorption_rate) < tolerance

    # Not using this as this absorption has raw counts of absorptions, which can differ by 20+ between runs
    # testing_utils.compare_dicts_within_tolerance(run_results, expected_results, tolerance)
