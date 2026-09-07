export interface AssessmentQuestion {
  id: string;
  text: string;
  options: { id: string; text: string }[];
  correct_answer: string;
  explanation: string;
  misconception?: string;
  remediation?: string[];
}

export const QUESTION_BANK: Record<"easy" | "medium" | "tough", AssessmentQuestion[]> = {
  easy: [
    {
      id: "q_easy_01",
      text: "What does P(A|B) denote in Bayesian probability?",
      options: [
        { id: "A", text: "The conditional probability of event A given that event B has occurred" },
        { id: "B", text: "The joint probability of events A and B occurring simultaneously" },
        { id: "C", text: "The marginal probability of event A occurring independently" },
        { id: "D", text: "The union probability of event A or event B" }
      ],
      correct_answer: "A",
      explanation: "P(A|B) is the conditional probability of A given B, calculated as P(A ∩ B) / P(B) when P(B) > 0.",
      misconception: "Do not confuse conditional probability P(A|B) with joint probability P(A ∩ B).",
      remediation: ["Review Bayes' theorem formulations.", "Practice computing conditional vs joint probabilities."]
    },
    {
      id: "q_easy_02",
      text: "Which of the following describes a Type I error in statistical hypothesis testing?",
      options: [
        { id: "A", text: "Failing to reject a false null hypothesis" },
        { id: "B", text: "Rejecting a true null hypothesis (false positive)" },
        { id: "C", text: "Accepting a true alternative hypothesis" },
        { id: "D", text: "Failing to reject a true null hypothesis" }
      ],
      correct_answer: "B",
      explanation: "A Type I error (alpha) occurs when the null hypothesis H0 is true, but we incorrectly reject it.",
      misconception: "Type I is a false positive (rejecting true H0); Type II is a false negative (failing to reject false H0).",
      remediation: ["Review the 2x2 hypothesis decision matrix.", "Understand alpha significance level thresholds."]
    },
    {
      id: "q_easy_03",
      text: "What is the defining characteristic of Simple Random Sampling Without Replacement (SRSWOR)?",
      options: [
        { id: "A", text: "Every distinct subset of n units has an equal probability of selection: 1 / (N choose n)" },
        { id: "B", text: "Units are sampled based on probability proportional to size" },
        { id: "C", text: "Only units with above-average values are included" },
        { id: "D", text: "Each sampled unit is immediately returned to the frame before the next draw" }
      ],
      correct_answer: "A",
      explanation: "Under SRSWOR, every sample of size n from population N has probability 1/C(N, n), and each unit's inclusion probability is n/N.",
      misconception: "Returning the unit before the next draw describes SRSWR (with replacement), not SRSWOR.",
      remediation: ["Study basic sampling design properties.", "Compare SRSWR with SRSWOR variance formulas."]
    },
    {
      id: "q_easy_04",
      text: "In a heavily right-skewed income distribution, which measure of central tendency is generally most representative?",
      options: [
        { id: "A", text: "Arithmetic Mean" },
        { id: "B", text: "Median" },
        { id: "C", text: "Mid-range" },
        { id: "D", text: "Standard Deviation" }
      ],
      correct_answer: "B",
      explanation: "The median is robust against extreme positive outliers and represents the 50th percentile, unlike the arithmetic mean.",
      misconception: "Mean is pulled heavily toward the tail of extreme values; median remains unaffected by outlier magnitude.",
      remediation: ["Examine skewness effects on summary statistics.", "Review MoSPI consumption expenditure reports."]
    },
    {
      id: "q_easy_05",
      text: "What is the mathematical relationship between the sample variance (s^2) and the standard deviation (s)?",
      options: [
        { id: "A", text: "Standard deviation is the positive square root of variance" },
        { id: "B", text: "Variance is the square root of standard deviation" },
        { id: "C", text: "Standard deviation is variance multiplied by sample size n" },
        { id: "D", text: "There is no functional relationship between them" }
      ],
      correct_answer: "A",
      explanation: "Standard deviation is expressed in the original units of measurement as the positive square root of variance.",
      misconception: "Remember variance is in squared units (e.g. rupees squared), while standard deviation is in original units (rupees).",
      remediation: ["Review foundational dispersion formulas.", "Practice calculating sample standard deviations."]
    },
    {
      id: "q_easy_06",
      text: "When constructing strata in Stratified Random Sampling, the primary objective is to make units:",
      options: [
        { id: "A", text: "Homogeneous within each stratum, and heterogeneous between strata" },
        { id: "B", text: "Heterogeneous within each stratum, and homogeneous between strata" },
        { id: "C", text: "Completely independent of auxiliary information" },
        { id: "D", text: "Equal in count across all geographic divisions" }
      ],
      correct_answer: "A",
      explanation: "Stratification achieves variance reduction when within-stratum variance is minimal and between-stratum variance is maximal.",
      misconception: "Heterogeneous within and homogeneous between is the goal of cluster sampling, NOT stratified sampling.",
      remediation: ["Contrast cluster sampling vs stratified sampling objectives.", "Review Neyman allocation principles."]
    },
    {
      id: "q_easy_07",
      text: "If a two-tailed hypothesis test yields a p-value of 0.02 at a significance level alpha = 0.05, what is the appropriate decision?",
      options: [
        { id: "A", text: "Reject the null hypothesis H0" },
        { id: "B", text: "Fail to reject the null hypothesis H0" },
        { id: "C", text: "Accept the null hypothesis as definitively proven" },
        { id: "D", text: "Discard the sample data and re-run without testing" }
      ],
      correct_answer: "A",
      explanation: "When the p-value is less than or equal to alpha (0.02 < 0.05), we reject the null hypothesis.",
      misconception: "P-value is not the probability that H0 is true, but the probability of observing data as extreme given H0 is true.",
      remediation: ["Review p-value rejection criteria.", "Study statistical significance vs practical significance."]
    },
    {
      id: "q_easy_08",
      text: "According to the Central Limit Theorem (CLT), as sample size n becomes sufficiently large, the sampling distribution of the sample mean tends toward:",
      options: [
        { id: "A", text: "A Normal distribution, regardless of the parent population distribution" },
        { id: "B", text: "A Uniform distribution between 0 and 1" },
        { id: "C", text: "The identical distribution shape of the parent population" },
        { id: "D", text: "A Chi-squared distribution with n-1 degrees of freedom" }
      ],
      correct_answer: "A",
      explanation: "For independent and identically distributed variables with finite variance, the normalized sum approaches standard normal N(0, 1).",
      misconception: "CLT applies to the distribution of sample means, not the distribution of individual raw observations.",
      remediation: ["Study CLT simulation and sampling distributions.", "Observe how normality emerges with n >= 30."]
    },
    {
      id: "q_easy_09",
      text: "What does a 95% Confidence Interval for a population mean strictly mean?",
      options: [
        { id: "A", text: "In repeated sampling, approximately 95% of constructed intervals will contain the true parameter" },
        { id: "B", text: "There is a 95% chance that the specific observed interval contains the population mean" },
        { id: "C", text: "95% of the values in the population fall inside this specific interval" },
        { id: "D", text: "The sample mean will match the population mean with 95% accuracy" }
      ],
      correct_answer: "A",
      explanation: "Frequentist confidence intervals describe the long-run coverage rate across hypothetical repeated samples.",
      misconception: "Once calculated, the parameter is fixed; either it is in the interval or not (0 or 1 probability).",
      remediation: ["Study the frequentist definition of confidence intervals.", "Contrast with Bayesian credible intervals."]
    },
    {
      id: "q_easy_10",
      text: "Which of the following constitutes a non-sampling error in a national survey?",
      options: [
        { id: "A", text: "Data entry errors and respondent recall bias" },
        { id: "B", text: "Variation arising solely from observing a sample rather than the full census" },
        { id: "C", text: "Standard error due to finite sample size n" },
        { id: "D", text: "Variance associated with simple random selection" }
      ],
      correct_answer: "A",
      explanation: "Non-sampling errors arise from measurement, coverage, non-response, processing, and recording errors across all survey stages.",
      misconception: "Sampling error decreases as sample size increases, but non-sampling error can persist or even increase with larger surveys.",
      remediation: ["Review Total Survey Error (TSE) frameworks.", "Read MoSPI field inspection guidelines."]
    },
    {
      id: "q_easy_11",
      text: "What type of statistical variable is 'Educational Qualification' (Primary, Secondary, Graduate, Postgraduate)?",
      options: [
        { id: "A", text: "Ordinal categorical variable" },
        { id: "B", text: "Nominal categorical variable" },
        { id: "C", text: "Continuous interval variable" },
        { id: "D", text: "Ratio variable" }
      ],
      correct_answer: "A",
      explanation: "Ordinal variables possess a natural ranking or hierarchy, but differences between categories cannot be quantified numerically.",
      misconception: "Nominal variables have no order (e.g. religion, state); ordinal variables have intrinsic ordering.",
      remediation: ["Review Stevens' levels of measurement: Nominal, Ordinal, Interval, Ratio."]
    },
    {
      id: "q_easy_12",
      text: "In survey methodology, what is the Unit Response Rate?",
      options: [
        { id: "A", text: "The ratio of completed interviews to eligible sample units selected in the frame" },
        { id: "B", text: "The number of questions answered divided by total questions in the schedule" },
        { id: "C", text: "The percentage of investigators who completed their field training" },
        { id: "D", text: "The fraction of data items validated by supervisory scrutiny" }
      ],
      correct_answer: "A",
      explanation: "Unit response rate measures participation: completed eligible interviews divided by total eligible sample units.",
      misconception: "Item response rate refers to specific questions answered; unit response rate refers to sampled households/enterprises.",
      remediation: ["Review AAPOR standard response rate definitions.", "Study non-response adjustment methods."]
    },
    {
      id: "q_easy_13",
      text: "What is Selection Bias in the context of survey sampling?",
      options: [
        { id: "A", text: "Systematic exclusion or underrepresentation of certain segments of the target population" },
        { id: "B", text: "Random fluctuation in estimates due to sample size" },
        { id: "C", text: "A typographical mistake made by field investigators" },
        { id: "D", text: "Choosing median instead of mean during data analysis" }
      ],
      correct_answer: "A",
      explanation: "Selection bias occurs when the sampling frame or selection mechanism systematically favors certain units over others.",
      misconception: "Selection bias is a systematic distortion (non-sampling error), not random chance variation.",
      remediation: ["Examine sampling frame undercoverage issues.", "Study probability sampling criteria."]
    },
    {
      id: "q_easy_14",
      text: "What does the Law of Large Numbers state about the sample average?",
      options: [
        { id: "A", text: "It converges in probability to the expected value of the population as sample size grows" },
        { id: "B", text: "It will always equal the population median when n > 100" },
        { id: "C", text: "Sample variance increases indefinitely with sample size" },
        { id: "D", text: "Every sample distribution becomes uniformly distributed" }
      ],
      correct_answer: "A",
      explanation: "The weak and strong laws of large numbers establish convergence of the sample mean to the true population expectation.",
      misconception: "Convergence is asymptotic; it does not mean individual small samples will be exactly equal to the expectation.",
      remediation: ["Review convergence modes: in probability vs almost surely."]
    },
    {
      id: "q_easy_15",
      text: "What is the primary purpose of a pilot survey (pre-test) in national statistical operations?",
      options: [
        { id: "A", text: "To test questionnaire clarity, field logistics, and estimate variance parameters before main rollout" },
        { id: "B", text: "To publish final official GDP figures early" },
        { id: "C", text: "To replace the decennial population census" },
        { id: "D", text: "To eliminate the need for random sampling in the main survey" }
      ],
      correct_answer: "A",
      explanation: "Pilot surveys test instruments, assess non-response tendencies, train master trainers, and obtain preliminary variance estimates.",
      misconception: "Pilot survey data is not meant for official release; it validates the survey apparatus and protocols.",
      remediation: ["Review NSS survey lifecycle stages from schedule design to field testing."]
    }
  ],

  medium: [
    {
      id: "q_med_01",
      text: "When should the Finite Population Correction (FPC) factor sqrt((N - n) / (N - 1)) be applied to the variance of the sample mean?",
      options: [
        { id: "A", text: "When sampling without replacement and the sampling fraction (n / N) exceeds 5%" },
        { id: "B", text: "Only when sampling with replacement from an infinite universe" },
        { id: "C", text: "Exclusively when the population size N is greater than 10 million" },
        { id: "D", text: "Whenever cluster sampling is conducted across two stages" }
      ],
      correct_answer: "A",
      explanation: "When n/N > 0.05 in without-replacement sampling, FPC accounts for the reduction in sampling variance as a substantial fraction of the universe is examined.",
      misconception: "Omitting FPC when n/N is large overestimates standard error and produces overly conservative confidence intervals.",
      remediation: ["Review Cochran's Sampling Techniques section on FPC.", "Calculate variance reductions with FPC in small administrative frames."]
    },
    {
      id: "q_med_02",
      text: "Under Neyman Optimal Allocation in Stratified Sampling with fixed total sample size n, the sample allocated to stratum h (n_h) is proportional to:",
      options: [
        { id: "A", text: "N_h * S_h (Stratum size multiplied by stratum standard deviation)" },
        { id: "B", text: "N_h / S_h (Stratum size divided by stratum variance)" },
        { id: "C", text: "S_h alone, independent of stratum population size" },
        { id: "D", text: "Equal distribution n / H across all strata" }
      ],
      correct_answer: "A",
      explanation: "Neyman allocation assigns n_h = n * (N_h * S_h) / sum(N_k * S_k), allocating larger samples to larger and more variable strata.",
      misconception: "Proportional allocation uses only N_h; Neyman optimal allocation also incorporates stratum standard deviation S_h.",
      remediation: ["Derive Neyman allocation using Lagrange multipliers.", "Compare variance under Proportional vs Neyman allocation."]
    },
    {
      id: "q_med_03",
      text: "How does Cluster Sampling fundamentally differ from Stratified Random Sampling in terms of selection?",
      options: [
        { id: "A", text: "In stratified sampling, samples are drawn from every stratum; in cluster sampling, only a sample of clusters is selected" },
        { id: "B", text: "Cluster sampling guarantees lower variance than stratified sampling for the same total n" },
        { id: "C", text: "Stratified sampling only works for geographic boundaries, whereas clustering only works for industries" },
        { id: "D", text: "Every unit inside every cluster is surveyed in stratified sampling" }
      ],
      correct_answer: "A",
      explanation: "Stratification samples all strata (reducing between-strata variance); clustering samples only selected clusters (trading precision for field cost efficiency).",
      misconception: "Cluster sampling usually increases sampling variance (Deff > 1) due to positive intra-cluster correlation, but drastically lowers travel costs.",
      remediation: ["Compare efficiency and administrative logistics between cluster and stratified designs."]
    },
    {
      id: "q_med_04",
      text: "What does a Design Effect (Deff) of 2.4 indicate about a complex survey design compared to Simple Random Sampling?",
      options: [
        { id: "A", text: "The complex design variance is 2.4 times larger than the variance of an SRS of identical size" },
        { id: "B", text: "The survey sample size can be reduced by 2.4 times without loss of precision" },
        { id: "C", text: "The standard error under the complex design is 2.4 times smaller than SRS" },
        { id: "D", text: "The non-response rate in the survey is 24%" }
      ],
      correct_answer: "A",
      explanation: "Deff = Var_complex / Var_srs. A Deff of 2.4 means complex variance is 2.4x SRS variance; the effective sample size is n_eff = n / 2.4.",
      misconception: "Deff represents variance inflation, not standard error inflation (which is Deft = sqrt(Deff) = 1.55).",
      remediation: ["Study Kish's Design Effect formulation: Deff = 1 + (m - 1) * rho.", "Practice computing effective sample size."]
    },
    {
      id: "q_med_05",
      text: "In MoSPI's Periodic Labour Force Survey (PLFS), what typically serves as the First Stage Unit (FSU)?",
      options: [
        { id: "A", text: "Census Enumeration Blocks (CEB) in urban areas and Villages in rural areas" },
        { id: "B", text: "Individual formal wage employees" },
        { id: "C", text: "Whole administrative districts" },
        { id: "D", text: "Commercial industrial complexes registered under ASI" }
      ],
      correct_answer: "A",
      explanation: "PLFS uses a two-stage stratified design where FSUs are Census villages (rural) and Urban Frame Survey (UFS) blocks (urban).",
      misconception: "Households are Ultimate Stage Units (USUs) or Second Stage Units (SSUs), not First Stage Units (FSUs).",
      remediation: ["Review PLFS sampling design and technical documentation from MoSPI.", "Study two-stage probability sampling."]
    },
    {
      id: "q_med_06",
      text: "A Variance Inflation Factor (VIF) greater than 10 in multiple regression analysis typically signifies:",
      options: [
        { id: "A", text: "Severe multicollinearity among explanatory predictors" },
        { id: "B", text: "Extreme heteroscedasticity in model residuals" },
        { id: "C", text: "Absence of any linear correlation with the dependent variable" },
        { id: "D", text: "That the R-squared value is exactly 0.10" }
      ],
      correct_answer: "A",
      explanation: "VIF = 1 / (1 - R_j^2). When VIF > 10, over 90% of the variance in predictor j is explained by other predictors, inflating standard errors.",
      misconception: "High VIF inflates coefficient variance, making estimates unstable, but does not bias OLS point predictions.",
      remediation: ["Explore principal component regression and ridge regularization for collinear features."]
    },
    {
      id: "q_med_07",
      text: "Under what conditions is the Ratio Estimator (y_hat_R = (y_bar / x_bar) * X) more efficient than the simple sample mean estimator y_bar?",
      options: [
        { id: "A", text: "When correlation rho(X, Y) > (CV(X) / (2 * CV(Y))) and the relationship is a straight line through origin" },
        { id: "B", text: "Whenever X and Y have negative linear correlation" },
        { id: "C", text: "Only when the sample size is less than 10" },
        { id: "D", text: "Exclusively when variable X has higher variance than variable Y" }
      ],
      correct_answer: "A",
      explanation: "Ratio estimation improves precision over SRS mean when auxiliary variable X is strongly positively correlated with Y such that rho > 0.5 * (CV_x / CV_y).",
      misconception: "Ratio estimator is slightly biased in small samples, but asymptotically unbiased and highly efficient for large n.",
      remediation: ["Review ratio and regression estimators in sampling theory.", "Examine bias order O(1/n)."]
    },
    {
      id: "q_med_08",
      text: "What is the primary statistical function of Post-Stratification weighting adjustments?",
      options: [
        { id: "A", text: "To align sample distribution marginals with known population benchmarks and mitigate non-response bias" },
        { id: "B", text: "To artificially increase the observed sample size" },
        { id: "C", text: "To discard records that have missing values" },
        { id: "D", text: "To replace field interviews with econometric forecasting" }
      ],
      correct_answer: "A",
      explanation: "Post-stratification adjusts design weights by N_h / (N * (n_h / n)) to match known census totals, reducing variance and differential non-response bias.",
      misconception: "Post-stratification does not alter data values; it calibrates unit weights so weighted sample sums equal population controls.",
      remediation: ["Study calibration and raking ratio estimation techniques in survey statistics."]
    },
    {
      id: "q_med_09",
      text: "In unequal probability sampling, the Horvitz-Thompson estimator of population total Y_total is expressed as:",
      options: [
        { id: "A", text: "Sum of (y_i / pi_i) for all sampled units i, where pi_i is unit inclusion probability" },
        { id: "B", text: "Sum of (y_i * pi_i) for all sampled units i" },
        { id: "C", text: "Arithmetic average of y multiplied by the frame count N" },
        { id: "D", text: "Product of sample median and total inclusion probabilities" }
      ],
      correct_answer: "A",
      explanation: "The Horvitz-Thompson estimator y_hat_HT = sum(y_i / pi_i) is strictly design-unbiased for any probability design where all pi_i > 0.",
      misconception: "Units are weighted by the inverse inclusion probability (design weight w_i = 1 / pi_i), not by pi_i directly.",
      remediation: ["Derive Horvitz-Thompson unbiasedness E[y_hat_HT] = Y.", "Study Sen-Yates-Grundy variance formula."]
    },
    {
      id: "q_med_10",
      text: "What is the principal vulnerability of 1-in-k Systematic Sampling when ordering is not random?",
      options: [
        { id: "A", text: "Severe bias and variance inflation if the sampling interval k coincides with a hidden periodic cycle in the frame" },
        { id: "B", text: "Inability to select any unit beyond the first interval" },
        { id: "C", text: "Zero probability of selecting large units" },
        { id: "D", text: "Extreme difficulty in drawing the initial random start" }
      ],
      correct_answer: "A",
      explanation: "If population units exhibit periodic cyclical variation with period k, systematic sampling can systematically select only peaks or troughs.",
      misconception: "Implicit stratification under systematic sampling is beneficial with monotone trends, but devastating with periodic trends.",
      remediation: ["Study systematic sampling under linear trends, periodic variations, and autocorrelated lists."]
    },
    {
      id: "q_med_11",
      text: "How does the Intraclass Correlation Coefficient (rho) within clusters affect the variance of cluster sampling?",
      options: [
        { id: "A", text: "Higher positive rho increases sampling variance because units within clusters provide redundant information" },
        { id: "B", text: "Positive rho reduces sampling variance toward zero" },
        { id: "C", text: "Rho has zero mathematical influence on cluster variance" },
        { id: "D", text: "Negative rho causes infinite design variance" }
      ],
      correct_answer: "A",
      explanation: "Variance is multiplied by Deff = 1 + (m - 1) * rho. When rho > 0, units in the same cluster are similar, diminishing effective independent information.",
      misconception: "Higher homogeneity within clusters hurts cluster sampling efficiency, whereas it improves stratified sampling efficiency.",
      remediation: ["Analyze the dual role of homogeneity in cluster vs stratified sampling."]
    },
    {
      id: "q_med_12",
      text: "In Probability Proportional to Size (PPS) sampling, what is the selection probability p_i of unit i in a single draw?",
      options: [
        { id: "A", text: "M_i / sum(M_k), where M_i is the auxiliary size measure of unit i" },
        { id: "B", text: "Constant 1 / N for all units regardless of size" },
        { id: "C", text: "sqrt(M_i) / n" },
        { id: "D", text: "M_i multiplied by the sampling interval" }
      ],
      correct_answer: "A",
      explanation: "PPS assigns draw probabilities proportional to an auxiliary size metric (e.g., village population or enterprise employment).",
      misconception: "PPS balances survey workload and reduces variance when size is strongly correlated with study variables.",
      remediation: ["Study cumulative total method and Lahiri's method for PPS selection."]
    },
    {
      id: "q_med_13",
      text: "Statistical power (1 - beta) in an evaluation study represents the probability of:",
      options: [
        { id: "A", text: "Correctly rejecting the null hypothesis when a true effect of given size exists" },
        { id: "B", text: "Committing a Type I error when H0 is true" },
        { id: "C", text: "Achieving an R-squared value above 0.90" },
        { id: "D", text: "Obtaining zero standard error in the sample" }
      ],
      correct_answer: "A",
      explanation: "Statistical power is the sensitivity of the test to detect an actual effect or policy difference, equal to 1 minus Type II error probability.",
      misconception: "Power is not 1 - alpha; alpha is significance level (Type I error), beta is Type II error.",
      remediation: ["Review sample size calculations based on Minimum Detectable Effect (MDE) and power 0.80."]
    },
    {
      id: "q_med_14",
      text: "What is the standard guidance regarding the Coefficient of Variation (CV = SE / Estimate) for publishing reliable official survey estimates?",
      options: [
        { id: "A", text: "Estimates with CV <= 15% are generally considered reliable for public dissemination; CV > 30% indicates caution/suppression" },
        { id: "B", text: "CV must be exactly 0.00% to publish any official table" },
        { id: "C", text: "Higher CV values always indicate superior precision" },
        { id: "D", text: "CV is only calculated for qualitative census counts" }
      ],
      correct_answer: "A",
      explanation: "Official statistical agencies (including MoSPI and international peers) tag estimates with CV > 20%-30% with cautionary flags due to sampling noise.",
      misconception: "A large point estimate can still have high CV if standard error is large relative to the estimate.",
      remediation: ["Review MoSPI quality standards for survey data dissemination and tabulations."]
    },
    {
      id: "q_med_15",
      text: "Which imputation method substitutes a missing value with the observed response from a similar unit matched on auxiliary variables?",
      options: [
        { id: "A", text: "Hot-Deck Imputation" },
        { id: "B", text: "Grand Mean Imputation" },
        { id: "C", text: "Zero Replacement" },
        { id: "D", text: "Deterministic Median Substitution" }
      ],
      correct_answer: "A",
      explanation: "Hot-deck imputation finds a 'donor' record within the same survey data file that matches the recipient on key conditioning variables.",
      misconception: "Cold-deck imputation uses historical/external surveys; hot-deck uses the current live survey dataset.",
      remediation: ["Compare hot-deck, nearest-neighbor donor imputation, and multiple imputation."]
    }
  ],

  tough: [
    {
      id: "q_tough_01",
      text: "In Double Sampling (Two-Phase Sampling) for stratification, why is a large first-phase sample n' drawn before selecting final sample n?",
      options: [
        { id: "A", text: "To estimate unknown stratum proportions W_h inexpensively before allocating the second-phase sample" },
        { id: "B", text: "To replace all face-to-face interviews with administrative register matching" },
        { id: "C", text: "To eliminate non-sampling error entirely from both phases" },
        { id: "D", text: "To guarantee that design effect Deff is zero" }
      ],
      correct_answer: "A",
      explanation: "When frame stratum weights W_h are unknown, a cheap first-phase sample estimates W_h, allowing optimal second-phase stratification for costly variables.",
      misconception: "Double sampling incurs variance from both phases; it is cost-effective only when first-phase observation is substantially cheaper than second-phase.",
      remediation: ["Derive variance of two-phase stratified estimator.", "Study Cochran Chapter 12 on Double Sampling."]
    },
    {
      id: "q_tough_02",
      text: "In Small Area Estimation (SAE), the Fay-Herriot model connects area-level direct survey estimators to auxiliary covariates using:",
      options: [
        { id: "A", text: "An empirical Bayes linear mixed model combining direct estimators with synthetic regression predictions based on area random effects" },
        { id: "B", text: "A deterministic polynomial spline without error components" },
        { id: "C", text: "A simple moving average of neighboring districts" },
        { id: "D", text: "A unweighted ordinary least squares regression ignoring survey weights" }
      ],
      correct_answer: "A",
      explanation: "The Fay-Herriot model: y_i = x_i' * beta + u_i + e_i, where u_i is area random effect and e_i is sampling error, borrowing strength across areas.",
      misconception: "Direct estimators have unacceptably large standard errors in small areas; SAE 'borrows strength' from administrative census data and other domains.",
      remediation: ["Read Rao & Molina's Small Area Estimation on area-level vs unit-level EBLUP models."]
    },
    {
      id: "q_tough_03",
      text: "Under Generalized Regression (GREG) calibration estimation, what core property do the calibrated weights w_k satisfy?",
      options: [
        { id: "A", text: "Sum of (w_k * x_k) exactly matches known population auxiliary totals X_total, while minimizing distance from design weights d_k" },
        { id: "B", text: "Calibrated weights must all be identical integers" },
        { id: "C", text: "Every calibrated weight is constrained to be strictly less than 1" },
        { id: "D", text: "Auxiliary variables are completely dropped from variance estimation" }
      ],
      correct_answer: "A",
      explanation: "Calibration weights minimize a distance metric G(w_k, d_k) subject to the calibration equation sum(w_k * x_ki) = X_total_i.",
      misconception: "GREG estimates are design-consistent; even if the assisting regression model is misspecified, asymptotic unbiasedness is preserved.",
      remediation: ["Study Deville and Särndal (1992) Calibration Estimators in Survey Sampling."]
    },
    {
      id: "q_tough_04",
      text: "Why is the Balanced Repeated Replication (BRR) method preferred over Jackknife for median variance estimation in 2-PSU stratified designs?",
      options: [
        { id: "A", text: "Jackknife variance estimation is known to be inconsistent for non-smooth estimators like quantiles and medians" },
        { id: "B", text: "BRR does not require knowing which strata units belong to" },
        { id: "C", text: "Jackknife cannot be run on modern multi-core computers" },
        { id: "D", text: "BRR eliminates the need for orthogonal Hadamard matrices" }
      ],
      correct_answer: "A",
      explanation: "Jackknife variance estimators fail consistency for non-smooth statistics (medians/quantiles); BRR (or bootstrap) preserves consistency.",
      misconception: "For smooth statistics (means, totals), Jackknife and BRR are both consistent; the divergence occurs specifically with rank/quantile statistics.",
      remediation: ["Review Shao and Tu's The Jackknife and Bootstrap in survey sampling."]
    },
    {
      id: "q_tough_05",
      text: "When calculating the Consumer Price Index (CPI), how does Hedonic Price Index modeling adjust for quality changes in consumer products?",
      options: [
        { id: "A", text: "It decomposes product price into implicit shadow prices of constituent product attributes using econometric regression" },
        { id: "B", text: "It drops all upgraded products and only tracks discontinued obsolete models" },
        { id: "C", text: "It assumes that all price increases are 100% pure inflation without quality improvements" },
        { id: "D", text: "It averages base-year retail prices without adjusting for packaging size or durability" }
      ],
      correct_answer: "A",
      explanation: "Hedonic regressions model ln(P) = f(attributes); when a model is replaced, the attribute differences quantify quality adjustments vs pure price change.",
      misconception: "Failing to account for quality improvements overstates CPI inflation (the Boskin Commission effect).",
      remediation: ["Review IMF and MoSPI CPI Manual guidance on hedonics and matched-model techniques."]
    },
    {
      id: "q_tough_06",
      text: "Under Rubin's Rules for Multiple Imputation (MI with m imputed datasets), total variance T is decomposed into:",
      options: [
        { id: "A", text: "Within-imputation variance W_bar plus (1 + 1/m) times between-imputation variance B" },
        { id: "B", text: "The difference between maximum and minimum imputed values" },
        { id: "C", text: "Between-imputation variance B divided by the sample size n" },
        { id: "D", text: "Within-imputation variance W_bar multiplied by degrees of freedom" }
      ],
      correct_answer: "A",
      explanation: "T = W_bar + (1 + 1/m) * B. The factor (1 + 1/m) accounts for simulation error due to drawing a finite number m of imputed datasets.",
      misconception: "Single imputation underestimates variance because standard software treats imputed values as known observed data; MI reflects imputation uncertainty.",
      remediation: ["Study Donald Rubin's Multiple Imputation for Nonresponse in Surveys (1987)."]
    },
    {
      id: "q_tough_07",
      text: "In district-level estimation, what is the key limitation of purely Synthetic Estimators when applied to an atypical district?",
      options: [
        { id: "A", text: "Severe bias because the synthetic estimator assumes the district strictly mirrors national or state-level subgroup relationships" },
        { id: "B", text: "Uncontrollable sampling variance that exceeds direct survey variance" },
        { id: "C", text: "Inability to compute point estimates for any domain" },
        { id: "D", text: "Requirement to survey every single enterprise in the district" }
      ],
      correct_answer: "A",
      explanation: "Synthetic estimators have very low variance but introduce significant bias when local area dynamics deviate from the broader regional average.",
      misconception: "Composite estimators solve this by taking an optimal weighted combination of the direct estimator and synthetic estimator.",
      remediation: ["Contrast synthetic, direct, and composite shrinkage estimators."]
    },
    {
      id: "q_tough_08",
      text: "What does the Durbin-Wu-Hausman test evaluate in an instrumental variables (IV) regression setting?",
      options: [
        { id: "A", text: "Whether an explanatory regressor is endogenous, comparing OLS and 2SLS coefficient estimates" },
        { id: "B", text: "Whether the regression error follows a standard Cauchy distribution" },
        { id: "C", text: "Whether sample size is sufficiently large for asymptotic chi-squared approximation" },
        { id: "D", text: "Whether heteroscedasticity is strictly homoscedastic" }
      ],
      correct_answer: "A",
      explanation: "Under H0 (exogeneity), OLS is efficient and consistent; under H1 (endogeneity), OLS is inconsistent but 2SLS is consistent. Hausman tests their difference.",
      misconception: "If regressors are exogenous, OLS is preferred due to smaller standard errors; IV/2SLS is less efficient and requires strong instruments.",
      remediation: ["Review instrument relevance (F > 10 rule) and exogeneity orthogonality conditions."]
    },
    {
      id: "q_tough_09",
      text: "In observational policy evaluation, why is trimming data outside the Common Support region of the Propensity Score essential?",
      options: [
        { id: "A", text: "To prevent extreme weights and biased counterfactual comparisons where treatment units have no comparable controls" },
        { id: "B", text: "To force the propensity score distribution to be uniform between 0 and 1" },
        { id: "C", text: "To ensure equal sample sizes in both treatment and control groups" },
        { id: "D", text: "To make the evaluation independent of baseline covariates" }
      ],
      correct_answer: "A",
      explanation: "Units lacking overlap violate the positivity/overlap assumption (0 < P(D=1|X) < 1), causing infinite inverse-propensity weights and extreme instability.",
      misconception: "Retaining units with propensity near 0 or 1 creates severe sensitivity to small specification changes.",
      remediation: ["Review Rosenbaum and Rubin (1983) and Imbens on causal inference and overlap diagnostics."]
    },
    {
      id: "q_tough_10",
      text: "What is the primary purpose of Generalized Variance Functions (GVF) in national statistical reports (like NSS / PLFS)?",
      options: [
        { id: "A", text: "To provide mathematical curves relating relative variance to estimate magnitude, smoothing direct SE estimates across thousands of tables" },
        { id: "B", text: "To conceal confidential microdata from independent researchers" },
        { id: "C", text: "To replace survey questionnaires with macro models" },
        { id: "D", text: "To enforce zero sampling error across all sub-state estimates" }
      ],
      correct_answer: "A",
      explanation: "GVF models RelVar(y_hat) = a + b / y_hat, allowing users to calculate approximate standard errors for any tabulated cell from simple model parameters.",
      misconception: "Direct SE calculation for thousands of complex domain estimates can be noisy; GVF stabilizes standard error estimates.",
      remediation: ["Study Wolter's Introduction to Variance Estimation, Chapter on Generalized Variance Functions."]
    },
    {
      id: "q_tough_11",
      text: "Under the Groves et al. Total Survey Error (TSE) framework, how is the measurement dimension distinguished from the representation dimension?",
      options: [
        { id: "A", text: "Measurement addresses 'what is captured' (construct validity, response error); representation addresses 'who is represented' (coverage, sampling, non-response)" },
        { id: "B", text: "Measurement concerns only sample size; representation concerns only software coding" },
        { id: "C", text: "Measurement is handled by supervisors; representation is handled exclusively by programmers" },
        { id: "D", text: "There is no theoretical distinction in survey methodology" }
      ],
      correct_answer: "A",
      explanation: "TSE cleanly bifurcates survey errors into observational/measurement errors (construct to answer to edit) and representation errors (target population to frame to respondents).",
      misconception: "Increasing sample size only affects sampling error under representation; it does not reduce construct or response errors.",
      remediation: ["Review Groves et al., Survey Methodology, Total Survey Error chapter."]
    },
    {
      id: "q_tough_12",
      text: "What trade-off is involved when trimming extreme survey weights in complex survey analysis?",
      options: [
        { id: "A", text: "Trading off a small increase in estimate bias to achieve a substantial reduction in sampling variance and mean squared error (MSE)" },
        { id: "B", text: "Achieving zero bias while allowing variance to become infinite" },
        { id: "C", text: "Eliminating the need to perform survey weighting altogether" },
        { id: "D", text: "Increasing both bias and variance simultaneously" }
      ],
      correct_answer: "A",
      explanation: "MSE = Bias^2 + Variance. Extreme weights produce massive variance; trimming to a threshold (e.g. 5x median weight) drastically cuts variance at minimal bias cost.",
      misconception: "Untrimmed weights are strictly unbiased, but their MSE can be much worse than trimmed weights due to volatility from outlier weights.",
      remediation: ["Study weight trimming algorithms and Potter's weight truncation methods."]
    },
    {
      id: "q_tough_13",
      text: "In seasonal adjustment of economic time series (e.g. quarterly GDP or IIP), what is the key difference between X-13ARIMA-SEATS and TRAMO-SEATS?",
      options: [
        { id: "A", text: "X-13 uses non-parametric Henderson moving average filter decomposition; SEATS uses model-based ARIMA signal extraction decomposition" },
        { id: "B", text: "X-13 can only handle annual data; SEATS only handles daily stock prices" },
        { id: "C", text: "TRAMO-SEATS does not allow calendar trading-day adjustments" },
        { id: "D", text: "Neither method is capable of detecting outlier shocks or level shifts" }
      ],
      correct_answer: "A",
      explanation: "X-11/X-13 applies empirical moving average filters, whereas SEATS performs stochastic ARIMA-model-based decomposition into trend, cycle, and seasonal signals.",
      misconception: "Both methods pre-adjust for calendar and trading-day effects using regARIMA or TRAMO before decomposition.",
      remediation: ["Review US Census Bureau X-13 and Bank of Spain TRAMO-SEATS technical manuals."]
    },
    {
      id: "q_tough_14",
      text: "When implementing the Rao-Wu-Yue Rescaling Bootstrap for stratified multi-stage designs with n_h PSUs, why is simple naive i.i.d. bootstrap invalid?",
      options: [
        { id: "A", text: "Naive bootstrap fails to account for clustering and stratification, yielding severely underestimated standard errors" },
        { id: "B", text: "Naive bootstrap requires more than 100 billion iterations" },
        { id: "C", text: "PSUs cannot be resampled with replacement under any algorithm" },
        { id: "D", text: "The sample mean cannot be computed after bootstrap resampling" }
      ],
      correct_answer: "A",
      explanation: "Survey bootstrap must resample m_h PSUs within stratum h and rescale weights by w_k * [ (1 - sqrt(m_h / (n_h - 1))) + sqrt(m_h / (n_h - 1)) * (n_h / m_h) * r_hi ] to mimic complex design variance.",
      misconception: "Resampling individual observations instead of clusters destroys the intra-cluster correlation structure.",
      remediation: ["Study Rao, Wu, and Yue (1992) Some Recent Work on Resampling Methods for Complex Surveys."]
    },
    {
      id: "q_tough_15",
      text: "In Differential Privacy (DP) microdata release, what does the privacy parameter epsilon (privacy loss budget) control?",
      options: [
        { id: "A", text: "The maximum bound on the ratio of output probability distributions whether any single individual's record is present or absent: exp(epsilon)" },
        { id: "B", text: "The exact percentage of records that must be randomly deleted from the release" },
        { id: "C", text: "The number of statistical queries that can be answered before encrypting the database" },
        { id: "D", text: "The standard deviation of survey sampling error" }
      ],
      correct_answer: "A",
      explanation: "A randomized mechanism M satisfies epsilon-DP if Pr[M(D1) in S] <= exp(epsilon) * Pr[M(D2) in S] for all neighboring datasets D1, D2 differing by one record.",
      misconception: "Smaller epsilon means stronger privacy protection and more added noise; larger epsilon means greater statistical accuracy but less privacy.",
      remediation: ["Study Dwork and Roth's The Algorithmic Foundations of Differential Privacy."]
    }
  ]
};
