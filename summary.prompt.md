**Summary :**
<current_domain_from_JIRA_or_Not_Assigned> Pre-Analysis is done for <Jira Ticket ID> with Error Timestamp at: <timestamp_with_UTC>.

================================================

**Rootcause/Initial findings** : <1 concise paragraph describing the most likely technical cause of the failure; prefer coredump evidence over fishbone when both are available>

**Effect** : <1 concise paragraph describing the user-visible impact or observed behavior, IF available, take image analysis findings into account for this section. Mention the source of the evidence for the effect description, for example "based on image analysis findings" or "based on user report".>

**Next Steps/Domain** : <DOMAIN SUGGESTION LOGIC - Follow these rules:

1. Compare defect evidence (crash type, faulting process, affected component) against each domain's description in the VALID DOMAINS list.
2. Select the domain whose description best matches the evidence.
3. Write: "Suggest assigning to <best_matching_domain> domain for further investigation." + 1-sentence justification citing specific evidence.
4. If the ticket's current domain already matches the evidence, confirm it: "Current domain <domain> appears correct because..."
The suggested domain MUST exist in the VALID DOMAINS list.>

**Remarks** : <duplicate, related, or similar ticket references from PaperAI/search results, or other important remarks, the remarks should be clear, concise. A simple list of Ticket IDs is not sufficient. Show results in tabular format Rank|Jira_Key|Similarity_score|Remark. If no remarks can be given just state N/A>


================================================

**Issue Timing and Classification :**

Issue is observed <when_in_lifecycle_or_reproduction_step> and is <defect_type_or_keyword>.

Use this line to classify both timing and symptom, for example coldboot, STR, runup, after unlock, after OTA, during lifecycle transition, black screen, short black screen, partial display missing, ANR, crash, reboot, audio loss.

**Log Files Referred :** <only list this when multiple relevant attachments or occurrences were used; otherwise write N/A>

If log references are needed, use JIRA attachment markup with basenames only:

- Exported DLTs: [^<exported_dlt_filename_or_zip>]
- Fishbone report: [^<fishbone_report_filename>]
- Coredump analysis summary: [^<coredump_analysis_summary_filename>]

Do not include absolute local workspace paths. The posting tool maps basenames to JIRA attachments.

**Tested software version:** <software version for the relevant ECU, taken from the fishbone report; otherwise N/A>

**Used HW details :** <only for Display or Graphics topics; provide a small Markdown table with display sample and ECU HW sample details from the fishbone report; otherwise N/A>

================================================

**Pre-analysis :**
Findings from fishbone [^<fishbone_report_filename_or_NA>]:
- <fishbone finding 1>
- <fishbone finding 2>
- <fishbone timing, software, ECU, or signal observations if relevant>
- <write N/A if fishbone analysis was not available>

Findings from coredump analysis summary [^<coredump_analysis_summary_filename_or_NA>]:
- <coredump finding 1>
- <crash type, faulting process, module, or key stack evidence>
- <root cause clue from coredump only>
- <write N/A if no coredump analysis exists>

Findings from image/video analysis [^<image_analysis_summary_filename_or_NA>]:
- <defect pattern summary from image analysis: defect type, affected unit, observed failure>
- <reference match from knowledge base: defect type keyword, domain responsibility>
- <confidence score and justification from visual evidence>
- <write N/A if no image/video analysis was performed>

================================================

This summary was generated with the assistance of AI.
Contact "Front desk Pre-Analysis Team" for more information.

================================================
