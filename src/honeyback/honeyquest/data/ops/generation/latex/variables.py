# Copyright 2024 Dynatrace LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Portions of this code, as identified in remarks, are provided under the
# Creative Commons BY-SA or the MIT license, and are provided without
# any warranty. In each of the remarks, we have provided attribution to the
# original creators and other attribution parties, along with the title of
# the code (if known) a copyright notice and a link to the license, and a
# statement indicating whether or not we have modified the code.

# pylint: disable-all
# mypy: ignore-errors

import re
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from scipy.stats import binomtest, chi2_contingency

from .....common.models.query import Query
from ....types import ConfusionMatrix, HoneyquestResults
from ....util.listutil import flatten
from ....util.metrics import classification_metrics, cse
from ...counting import get_paired_query_ids, get_query_counts
from ...reporting import get_number_of_honeywires_with_citation_keys
from .constants import TYPE_NAMES_ABBRV


def store_latex_variables(
    path: str,
    preinit: Dict[str, str],
    results: Dict[str, HoneyquestResults],
    marks: pd.DataFrame,
    responses: pd.DataFrame,
    response_ids: pd.DataFrame,
    users: pd.DataFrame,
    queries_df: pd.DataFrame,
    queries_dict: Dict[str, Query],
    buckets: Dict[str, List[str]],
    id_dcpt: pd.DataFrame,
    id_risk: pd.DataFrame,
    aspect6a: pd.DataFrame,
    aspect6b: pd.DataFrame,
    aspect6c: pd.DataFrame,
    cm_trap: ConfusionMatrix,
    cm_hack: ConfusionMatrix,
    aspect1: pd.DataFrame,
    aspect3_dcpt: pd.DataFrame,
    aspect3_risk: pd.DataFrame,
    aspect2: pd.DataFrame,
    aspect4: pd.DataFrame,
):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    # flatten the query index and filter the queries
    query_index = set(flatten(buckets.values()))  # noqa: indirect use in the next line
    queries_df = queries_df.query("qid in @query_index")

    qur_neut = queries_df.query("query_label == 'neutral'")
    qur_dcpt = queries_df.query("query_label == 'deceptive'")
    qur_risk = queries_df.query("query_label == 'risky'")

    usr_ctf = users.query("eid == 'ctf1'")
    usr_res = users.query("eid == 'ex1'")

    usr_phasea = users.query("first_seen < '2023-05-01T00:00Z'")
    usr_ctf_phasea = usr_phasea.query("eid == 'ctf1'")
    usr_res_phasea = usr_phasea.query("eid == 'ex1'")

    usr_phaseb = users.query("first_seen >= '2023-05-01T00:00Z'")
    usr_ctf_phaseb = usr_phaseb.query("eid == 'ctf1'")
    usr_res_phaseb = usr_phaseb.query("eid == 'ex1'")
    usr_res_phaseb_incent = usr_res.query("first_seen > '2024-01-23T12:25Z'")
    usr_res_phaseb_eligible = usr_res_phaseb.query("num_answers >= 87")

    usr_students_ratio = users.query("job == 'student'").uid.nunique() / users.uid.nunique()

    resp_times = marks.groupby("rid").response_time.first()

    query_counts_dict = get_query_counts(results)
    query_counts = np.array(list(query_counts_dict.values()))
    paired_queries = get_paired_query_ids(queries_df)

    aspect6_max = aspect6a.max(axis=1)
    aspect6c_risk = aspect6c.loc[0, "num_risky_lines"] + aspect6c.loc[1, "num_risky_lines"]
    aspect6c_dcpt = aspect6c.loc[0, "num_deceptive_lines"] + aspect6c.loc[1, "num_deceptive_lines"]

    aspect3_dcpt_binom_pvalue_min = aspect3_dcpt.query(
        f"n >= {preinit['AspectTwoMinimumSampleSize']}"
    ).pvalue.min()

    mt_trap = classification_metrics(cm_trap)
    mt_hack = classification_metrics(cm_hack)

    fell_tp_deceptive = aspect1.loc["deceptive", "fell_tp"] / aspect1.loc["deceptive", "n"]
    mark_traps_first = aspect3_dcpt.loc["all", "k"] / aspect3_dcpt.loc["all", "n"]
    mark_risks_first = aspect3_risk.loc["all", "k"] / aspect3_risk.loc["all", "n"]

    fell_tp_deceptive_cse = cse(aspect1.loc["deceptive", "fell_tp"], aspect1.loc["deceptive", "n"])

    num_reject_null_ct = (aspect2.loc[aspect2.index != "all", "pvalue"] < 0.05).sum()
    num_a2_sample_size = aspect2.loc[
        "all", [(False, False), (False, True), (True, False), (True, True)]
    ].sum()

    content_length_mask = marks.mrk_line.str.lower().str.contains("content-length").fillna(False)
    content_length_mark_num = content_length_mask.sum()
    content_length_mark_ratio = content_length_mark_num / marks.shape[0]

    rowe_df = responses.merge(response_ids, on="rid", how="left", validate="1:1")
    rowe_df_dcpt = rowe_df.query("qid == 'TR849.filesystem.rowe.home-cooper'")
    rowe_df_ntrl = rowe_df.query("qid == 'TR849.filesystem.rowe.home-gaitan'")

    rowe_dcpt_hack = rowe_df_dcpt.ans_any_hack.sum() / rowe_df_dcpt.shape[0]
    rowe_dcpt_trap = rowe_df_dcpt.ans_any_trap.sum() / rowe_df_dcpt.shape[0]
    rowe_dcpt_hack_cse = cse(rowe_df_dcpt.ans_any_hack.sum(), rowe_df_dcpt.shape[0])
    rowe_dcpt_trap_cse = cse(rowe_df_dcpt.ans_any_trap.sum(), rowe_df_dcpt.shape[0])

    rowe_ntrl_hack = rowe_df_ntrl.ans_any_hack.sum() / rowe_df_ntrl.shape[0]
    rowe_ntrl_trap = rowe_df_ntrl.ans_any_trap.sum() / rowe_df_ntrl.shape[0]
    rowe_ntrl_hack_cse = cse(rowe_df_ntrl.ans_any_hack.sum(), rowe_df_ntrl.shape[0])
    rowe_ntrl_trap_cse = cse(rowe_df_ntrl.ans_any_trap.sum(), rowe_df_ntrl.shape[0])

    mark_ssh_mask = aspect4.index.str.lower().str.contains(".ssh")
    mark_bash_history_mask = aspect4.index.str.lower().str.contains(".bash_history")
    mark_data_csv_mask = aspect4.index.str.lower().str.contains("data.csv")
    mark_mod_header_mask = aspect4.index.str.lower().str.contains("mod_")

    mark_ssh_hack = aspect4[mark_ssh_mask].mrk_hack.sum()
    mark_bash_history_hack = aspect4[mark_bash_history_mask].mrk_hack.sum()
    mark_data_csv_hack = aspect4[mark_data_csv_mask].mrk_hack.sum()
    mark_mod_header_hack = aspect4[mark_mod_header_mask].mrk_hack.sum()

    mark_ssh_trap = aspect4[mark_ssh_mask].mrk_trap.sum()
    mark_bash_history_trap = aspect4[mark_bash_history_mask].mrk_trap.sum()
    mark_data_csv_trap = aspect4[mark_data_csv_mask].mrk_trap.sum()
    mark_mod_header_trap = aspect4[mark_mod_header_mask].mrk_trap.sum()

    num_cdts_with_ref = get_number_of_honeywires_with_citation_keys(
        id_dcpt.index, queries_df, queries_dict
    )
    num_cdts_without_ref = len(id_dcpt.index) - num_cdts_with_ref

    def __test_risky_deceptive_independence():
        # chi2 test for independence of exploit marks on deceptive and risky queries
        risk_mark = aspect1.loc["risky", "hack_tp"]
        risk_other = aspect1.loc["risky", "n"] - risk_mark
        dcpt_mark = aspect1.loc["deceptive", "fell_tp"]
        dcpt_other = aspect1.loc["deceptive", "n"] - dcpt_mark
        tab = [[risk_mark, dcpt_mark], [risk_other, dcpt_other]]

        return chi2_contingency(tab).pvalue

    def __test_opposite_mark_preference(df: pd.DataFrame):
        k, n = df.loc["all", ["k", "n"]].astype(int)
        return binomtest(k, n, p=0.5, alternative="less").pvalue

    variables = {
        **preinit,
        "AbbrvFilesystem": TYPE_NAMES_ABBRV["filesystem"],
        "AbbrvHttpheaders": TYPE_NAMES_ABBRV["httpheaders"],
        "AbbrvNetworkrequests": TYPE_NAMES_ABBRV["networkrequests"],
        "AbbrvHtaccess": TYPE_NAMES_ABBRV["htaccess"],
        #
        "NumMarks": "{:,d}".format(len(marks)),
        "NumResponses": "{:,d}".format(len(responses)),
        "NumAvgMarksPerResponse": "{:.1f}".format(len(marks) / len(responses)),
        #
        "NumTotalQueryLines": "{:,d}".format(queries_df.num_lines.sum()),
        "NumTotalRiskyLines": "{:,d}".format(queries_df.num_risky_lines.sum()),
        "NumTotalRiskyLinesPercent": "{:.2f}".format(
            queries_df.num_risky_lines.sum() / queries_df.num_lines.sum() * 100
        ),
        "NumTotalDeceptiveLines": "{:,d}".format(queries_df.num_deceptive_lines.sum()),
        "NumTotalDeceptiveLinesPercent": "{:.2f}".format(
            queries_df.num_deceptive_lines.sum() / queries_df.num_lines.sum() * 100
        ),
        #
        "NumCDTs": "{:,d}".format(len(id_dcpt.index)),
        "NumRisks": "{:,d}".format(len(id_risk.index)),
        "NumCDTsWithLiteratureRef": "{:,d}".format(num_cdts_with_ref),
        "NumCDTsWithoutLiteratureRef": "{:,d}".format(num_cdts_without_ref),
        #
        "NumParticipants": users.uid.nunique(),
        "NumParticipantsPhaseA": usr_phasea.uid.nunique(),
        "NumParticipantsPhaseB": usr_phaseb.uid.nunique(),
        "NumParticipantsCtf": usr_ctf.uid.nunique(),
        "NumParticipantsCtfPhaseA": usr_ctf_phasea.uid.nunique(),
        "NumParticipantsCtfPhaseB": usr_ctf_phaseb.uid.nunique(),
        "NumParticipantsRes": usr_res.uid.nunique(),
        "NumParticipantsResPhaseA": usr_res_phasea.uid.nunique(),
        "NumParticipantsResPhaseB": usr_res_phaseb.uid.nunique(),
        "NumParticipantsResIncentivized": usr_res_phaseb_incent.uid.nunique(),
        "NumParticipantsResEligible": usr_res_phaseb_eligible.uid.nunique(),
        "NumParticipantsResLotteryPlayers": 1,
        "NumParticipantsStudentsRatio": "{:.0f}".format(usr_students_ratio * 100),
        #
        "NumParticipantsCtfManagers": usr_ctf.query("job == 'biz'").uid.nunique(),
        "NumParticipantsCtfDevelopers": usr_ctf.query("job == 'dev'").uid.nunique(),
        "NumParticipantsCtfResearcher": usr_ctf.query("job == 'research'").uid.nunique(),
        "NumParticipantsCtfStudents": usr_ctf.query("job == 'student'").uid.nunique(),
        "NumParticipantsCtfOps": usr_ctf.query("job == 'ops'").uid.nunique(),
        "NumParticipantsCtfSecOps": usr_ctf.query("job == 'secops'").uid.nunique(),
        #
        "NumParticipantsResManagers": usr_res.query("job == 'biz'").uid.nunique(),
        "NumParticipantsResDevelopers": usr_res.query("job == 'dev'").uid.nunique(),
        "NumParticipantsResResearcher": usr_res.query("job == 'research'").uid.nunique(),
        "NumParticipantsResStudents": usr_res.query("job == 'student'").uid.nunique(),
        "NumParticipantsResOps": usr_res.query("job == 'ops'").uid.nunique(),
        "NumParticipantsResSecOps": usr_res.query("job == 'secops'").uid.nunique(),
        #
        "NumParticipantsCtfYearsMedian": int(usr_ctf.years.median()),
        "NumParticipantsCtfYearsMean": "{:.1f}".format(usr_ctf.years.mean()),
        "NumParticipantsResYearsMedian": int(usr_res.years.median()),
        "NumParticipantsResYearsMean": "{:.1f}".format(usr_res.years.mean()),
        #
        "NumQueries": len(queries_df),
        "NumQueriesNeutral": len(qur_neut),
        "NumQueriesDeceptive": len(qur_dcpt),
        "NumQueriesRisky": len(qur_risk),
        #
        "NumQueriesFilesystem": len(queries_df.query("query_type == 'filesystem'")),
        "NumQueriesFilesystemNeut": len(qur_neut.query("query_type == 'filesystem'")),
        "NumQueriesFilesystemDcpt": len(qur_dcpt.query("query_type == 'filesystem'")),
        "NumQueriesFilesystemRisk": len(qur_risk.query("query_type == 'filesystem'")),
        #
        "NumQueriesHttpHeaders": len(queries_df.query("query_type == 'httpheaders'")),
        "NumQueriesHttpHeadersNeut": len(qur_neut.query("query_type == 'httpheaders'")),
        "NumQueriesHttpHeadersDcpt": len(qur_dcpt.query("query_type == 'httpheaders'")),
        "NumQueriesHttpHeadersRisk": len(qur_risk.query("query_type == 'httpheaders'")),
        #
        "NumQueriesHtaccess": len(queries_df.query("query_type == 'htaccess'")),
        "NumQueriesHtaccessNeut": len(qur_neut.query("query_type == 'htaccess'")),
        "NumQueriesHtaccessDcpt": len(qur_dcpt.query("query_type == 'htaccess'")),
        "NumQueriesHtaccessRisk": len(qur_risk.query("query_type == 'htaccess'")),
        #
        "NumQueriesNetworkRequests": len(queries_df.query("query_type == 'networkrequests'")),
        "NumQueriesNetworkRequestsNeut": len(qur_neut.query("query_type == 'networkrequests'")),
        "NumQueriesNetworkRequestsDcpt": len(qur_dcpt.query("query_type == 'networkrequests'")),
        "NumQueriesNetworkRequestsRisk": len(qur_risk.query("query_type == 'networkrequests'")),
        #
        "NumCDTsWithRiskyAndDeceptiveQueries": "{:d}".format(aspect2.shape[0] - 1),
        "NumPairedQueries": "{:d}".format(paired_queries.shape[0]),
        #
        "ResAnswerTimeMedian": "{:.0f}".format(resp_times.median()),
        "ResAnswerTimeMean": "{:.1f}".format(resp_times.mean()),
        #
        "ResAnswerQueriesMedian": "{:.0f}".format(np.median(query_counts)),
        "ResAnswerQueriesMean": "{:.0f}".format(np.mean(query_counts)),
        #
        "RatioVariantExactMax": "{:.2f}".format(aspect6_max["exact"]),
        "RatioVariantNoneMax": "{:.2f}".format(aspect6_max["none"]),
        "RatioVariantOtherMax": "{:.2f}".format(aspect6_max["other"]),
        "RatioVariantOverlapMax": "{:.2f}".format(aspect6_max["overlap"]),
        "RatioVariantSubsetMax": "{:.2f}".format(aspect6_max["subset"]),
        #
        "RatioAnswerAllMarked": "{:.2f}".format(aspect6b.loc[True, "ans_all"]),
        "RatioQueriesWithGtOneRiskyLine": "{:.2f}".format(100 - aspect6c_risk),
        "RatioQueriesWithGtOneDeceptiveLine": "{:.2f}".format(100 - aspect6c_dcpt),
        #
        "ResCmDcptTn": cm_trap.tn,
        "ResCmDcptFp": cm_trap.fp,
        "ResCmDcptFn": cm_trap.fn,
        "ResCmDcptTp": cm_trap.tp,
        "ResCmDcptAccRaw": "{:.2f}".format(mt_trap["acc"]).lstrip("0"),
        "ResCmDcptPpvRaw": "{:.2f}".format(mt_trap["ppv"]).lstrip("0"),
        "ResCmDcptTprRaw": "{:.2f}".format(mt_trap["tpr"]).lstrip("0"),
        "ResCmDcptFprRaw": "{:.2f}".format(mt_trap["fpr"]).lstrip("0"),
        "ResCmDcptFoneRaw": "{:.2f}".format(mt_trap["f1"]).lstrip("0"),
        "ResCmDcptMccRaw": "{:.2f}".format(mt_trap["mcc"]).lstrip("0"),
        "ResCmDcptAcc": "{:.0f}".format(mt_trap["acc"] * 100),
        "ResCmDcptPpv": "{:.0f}".format(mt_trap["ppv"] * 100),
        "ResCmDcptTpr": "{:.0f}".format(mt_trap["tpr"] * 100),
        "ResCmDcptFpr": "{:.0f}".format(mt_trap["fpr"] * 100),
        "ResCmDcptFone": "{:.0f}".format(mt_trap["f1"] * 100),
        "ResCmDcptMcc": "{:.0f}".format(mt_trap["mcc"] * 100),
        "ResCmDcptAccCse": "{:.1f}".format(mt_trap["acc_cse"] * 100),
        "ResCmDcptPpvCse": "{:.1f}".format(mt_trap["ppv_cse"] * 100),
        "ResCmDcptTprCse": "{:.1f}".format(mt_trap["tpr_cse"] * 100),
        "ResCmDcptFprCse": "{:.1f}".format(mt_trap["fpr_cse"] * 100),
        #
        "ResCmRiskTn": cm_hack.tn,
        "ResCmRiskFp": cm_hack.fp,
        "ResCmRiskFn": cm_hack.fn,
        "ResCmRiskTp": cm_hack.tp,
        "ResCmRiskAccRaw": "{:.2f}".format(mt_hack["acc"]).lstrip("0"),
        "ResCmRiskPpvRaw": "{:.2f}".format(mt_hack["ppv"]).lstrip("0"),
        "ResCmRiskTprRaw": "{:.2f}".format(mt_hack["tpr"]).lstrip("0"),
        "ResCmRiskFprRaw": "{:.2f}".format(mt_hack["fpr"]).lstrip("0"),
        "ResCmRiskFoneRaw": "{:.2f}".format(mt_hack["f1"]).lstrip("0"),
        "ResCmRiskMccRaw": "{:.2f}".format(mt_hack["mcc"]).lstrip("0"),
        "ResCmRiskAcc": "{:.0f}".format(mt_hack["acc"] * 100),
        "ResCmRiskPpv": "{:.0f}".format(mt_hack["ppv"] * 100),
        "ResCmRiskTpr": "{:.0f}".format(mt_hack["tpr"] * 100),
        "ResCmRiskFpr": "{:.0f}".format(mt_hack["fpr"] * 100),
        "ResCmRiskFone": "{:.0f}".format(mt_hack["f1"] * 100),
        "ResCmRiskMcc": "{:.0f}".format(mt_hack["mcc"] * 100),
        "ResCmRiskAccCse": "{:.1f}".format(mt_hack["acc_cse"] * 100),
        "ResCmRiskPpvCse": "{:.1f}".format(mt_hack["ppv_cse"] * 100),
        "ResCmRiskTprCse": "{:.1f}".format(mt_hack["tpr_cse"] * 100),
        "ResCmRiskFprCse": "{:.1f}".format(mt_hack["fpr_cse"] * 100),
        #
        "ResFellTpDcpt": "{:.0f}".format(fell_tp_deceptive * 100),
        "ResFellTpDcptCse": "{:.1f}".format(fell_tp_deceptive_cse * 100),
        #
        "ResTrapsFirstOverall": "{:.0f}".format(mark_traps_first * 100),
        "ResRisksFirstOverall": "{:.0f}".format(mark_risks_first * 100),
        #
        "ResBeforeAfterOverallPvalue": "{:.4f}".format(aspect2.loc["all", "pvalue"]),
        "ResBeforeAfterOverallRiskReduction": "{:.0f}".format(-aspect2.loc["all", "rr%"]),
        "ResBeforeAfterNumRejectNull": "{:d}".format(num_reject_null_ct),
        #
        "ResTestRiskDcptMarksPvalue": "{:.4f}".format(__test_risky_deceptive_independence()),
        "ResTestRiskDcptMarksNumRisky": "{:d}".format(aspect1.loc["risky", "n"]),
        "ResTestRiskDcptMarksNumDeceptive": "{:d}".format(aspect1.loc["deceptive", "n"]),
        "ResTestRiskDcptMarksNumTotal": "{:d}".format(
            aspect1.loc["risky", "n"] + aspect1.loc["deceptive", "n"]
        ),
        "ResTestMarkPreferenceDcptPvalue": "{:.4f}".format(aspect3_dcpt.loc["all", "pvalue"]),
        "ResTestMarkPreferenceRiskPvalue": "{:.4f}".format(aspect3_risk.loc["all", "pvalue"]),
        "ResTestMarkPreferenceDcptOppositePvalue": "{:.8f}".format(
            __test_opposite_mark_preference(aspect3_dcpt)
        ),
        "ResTestMarkPreferenceRiskOppositePvalue": "{:.8f}".format(
            __test_opposite_mark_preference(aspect3_risk)
        ),
        #
        "ResContentLengthMarkNum": "{:d}".format(content_length_mark_num),
        "ResContentLengthMarkRatio": "{:.2f}".format(content_length_mark_ratio * 100),
        #
        "ResRoweDeceptiveHack": "{:.0f}".format(rowe_dcpt_hack * 100),
        "ResRoweDeceptiveTrap": "{:.0f}".format(rowe_dcpt_trap * 100),
        "ResRoweNeutralHack": "{:.0f}".format(rowe_ntrl_hack * 100),
        "ResRoweNeutralTrap": "{:.0f}".format(rowe_ntrl_trap * 100),
        "ResRoweDeceptiveHackCse": "{:.1f}".format(rowe_dcpt_hack_cse * 100),
        "ResRoweDeceptiveTrapCse": "{:.1f}".format(rowe_dcpt_trap_cse * 100),
        "ResRoweNeutralHackCse": "{:.1f}".format(rowe_ntrl_hack_cse * 100),
        "ResRoweNeutralTrapCse": "{:.1f}".format(rowe_ntrl_trap_cse * 100),
        #
        "ResNumHackMarksOnLineSsh": "{:d}".format(mark_ssh_hack),
        "ResNumHackMarksOnLineBashHistory": "{:d}".format(mark_bash_history_hack),
        "ResNumHackMarksOnLineDataCsv": "{:d}".format(mark_data_csv_hack),
        "ResNumHackMarksOnLineModHeader": "{:d}".format(mark_mod_header_hack),
        "ResNumTrapMarksOnLineSsh": "{:d}".format(mark_ssh_trap),
        "ResNumTrapMarksOnLineBashHistory": "{:d}".format(mark_bash_history_trap),
        "ResNumTrapMarksOnLineDataCsv": "{:d}".format(mark_data_csv_trap),
        "ResNumTrapMarksOnLineModHeader": "{:d}".format(mark_mod_header_trap),
        "AspectTwoOverallSampleSize": num_a2_sample_size,
        "AspectThreeDcptOverallSampleSize": aspect3_dcpt.loc["all", "n"],
        "AspectThreeRiskOverallSampleSize": aspect3_risk.loc["all", "n"],
        "AspectRankedFirstMinimumPvalue": "{:.4f}".format(aspect3_dcpt_binom_pvalue_min),
        #
        "NumParticipantsAndDroppedUsers": preinit["NumDroppedUsers"] + users.uid.nunique(),
        "NumMinimumResponses": preinit["NumMinimumResponsesWithoutTutorial"] + 8,
    }

    # auto-generate all deceptive and risky ids
    all_dcpt_ids = {f"IdDcpt{query_id_to_latex(idd)}": id_dcpt.loc[idd][0] for idd in id_dcpt.index}
    all_risk_ids = {f"IdRisk{query_id_to_latex(idd)}": id_risk.loc[idd][0] for idd in id_risk.index}
    variables.update(all_dcpt_ids)
    variables.update(all_risk_ids)

    # auto-generate all deceptive and risky ratios and scaled standard errors
    for dcpt in id_dcpt.index:
        row = aspect1.query("applied_honeywire == @dcpt").iloc[0]
        fell_tp_ratio = (row["fell_tp"] / row["n"]) * 100
        trap_tp_ratio = (row["trap_tp"] / row["n"]) * 100
        dcpt_fn_ratio = (row["dcpt_fn_skip"] / row["n"]) * 100
        variables[f"ResRatioDcptFellTp{query_id_to_latex(dcpt)}"] = "{:.0f}".format(fell_tp_ratio)
        variables[f"ResRatioDcptTrapTp{query_id_to_latex(dcpt)}"] = "{:.0f}".format(trap_tp_ratio)
        variables[f"ResRatioDcptDcptFn{query_id_to_latex(dcpt)}"] = "{:.0f}".format(dcpt_fn_ratio)

        fell_tp_cse = row["fell_tp_cse"] * 100
        trap_tp_cse = row["trap_tp_cse"] * 100
        dcpt_fn_cse = row["dcpt_fn_skip_cse"] * 100
        variables[f"ResCseDcptFellTp{query_id_to_latex(dcpt)}"] = "{:.1f}".format(fell_tp_cse)
        variables[f"ResCseDcptTrapTp{query_id_to_latex(dcpt)}"] = "{:.1f}".format(trap_tp_cse)
        variables[f"ResCseDcptDcptFn{query_id_to_latex(dcpt)}"] = "{:.1f}".format(dcpt_fn_cse)

    for risk in id_risk.index:
        row = aspect1.query("present_risk == @risk").iloc[0]
        hack_tp_ratio = (row["hack_tp"] / row["n"]) * 100
        new_tp_ratio = (row["new_tp"] / row["n"]) * 100
        risk_fn_ratio = (row["risk_fn_skip"] / row["n"]) * 100
        variables[f"ResRatioRiskHackTp{query_id_to_latex(risk)}"] = "{:.0f}".format(hack_tp_ratio)
        variables[f"ResRatioRiskNewTp{query_id_to_latex(risk)}"] = "{:.0f}".format(new_tp_ratio)
        variables[f"ResRatioRiskRiskFn{query_id_to_latex(risk)}"] = "{:.0f}".format(risk_fn_ratio)

        hack_tp_cse = row["hack_tp_cse"] * 100
        new_tp_cse = row["new_tp_cse"] * 100
        risk_fn_cse = row["risk_fn_skip_cse"] * 100
        variables[f"ResCseRiskHackTp{query_id_to_latex(risk)}"] = "{:.1f}".format(hack_tp_cse)
        variables[f"ResCseRiskNewTp{query_id_to_latex(risk)}"] = "{:.1f}".format(new_tp_cse)
        variables[f"ResCseRiskRiskFn{query_id_to_latex(risk)}"] = "{:.1f}".format(risk_fn_cse)

    # auto-generate contigency table results
    for dcpt in id_dcpt.index:
        if dcpt not in aspect2.index:
            continue
        ctn_rr = aspect2.loc[dcpt, "rr%"] * -1.0
        ctn_pvalue = aspect2.loc[dcpt, "pvalue"]
        variables[f"ResBeforeAfter{query_id_to_latex(dcpt)}RiskReduction"] = "{:.0f}".format(ctn_rr)
        variables[f"ResBeforeAfter{query_id_to_latex(dcpt)}Pvalue"] = "{:.4f}".format(ctn_pvalue)

    # semantic checks for claims that we make in the paper
    assert float(variables["AspectRankedFirstMinimumPvalue"]) > 0.05
    assert int(variables["ResNumTrapMarksOnLineBashHistory"]) == 0
    assert int(variables["ResRatioDcptTrapTpNetworkrequestsCleartextPassword"]) <= int(
        variables["ResRatioDcptTrapTpFilesystemPasswords"]
    )
    assert int(variables["ResRatioDcptFellTpNetworkrequestsMassAssignment"]) >= int(
        variables["ResRatioDcptFellTpNetworkrequestsLogEndpoint"]
    )
    assert int(variables["ResRatioDcptTrapTpNetworkrequestsLogEndpoint"]) >= int(
        variables["ResRatioDcptTrapTpNetworkrequestsMassAssignment"]
    )
    assert int(variables["ResRatioRiskHackTpHttpheadersOutdatedPhp"]) <= min(
        int(variables["ResRatioRiskHackTpHttpheadersOutdatedApache"]),
        int(variables["ResRatioRiskHackTpNetworkrequestsPasswordHashesInQueryParameters"]),
    )
    assert int(variables["ResRatioDcptFellTpHttpheadersAdminCookie"]) <= int(
        variables["ResRatioDcptFellTpHttpheadersDevtoken"]
    )
    assert int(variables["ResNumTrapMarksOnLineSsh"]) >= max(
        int(variables["ResNumTrapMarksOnLineBashHistory"]),
        int(variables["ResNumTrapMarksOnLineDataCsv"]),
    )

    with open(path, "w") as f:
        for k, v in sorted(variables.items(), key=lambda kv: kv[0]):
            f.write(f"\\newcommand{{\\Var{k}}}{{{v}}}\n")


def query_id_to_latex(text: str, prefix: str = "", suffix: str = ""):
    text = text.replace("/", "-")
    text = re.sub(r"[^A-Za-z-]", "", text)
    text = [e.capitalize() for e in text.split("-")]
    text = "".join(text)
    return f"{prefix}{text}{suffix}"
