# Research: Social Security 2027

Every number in the script is listed here with the words it comes from. The full text of each source is saved in `sources/`.

## Source 1: SSA news release, October 14, 2026
https://content.govdelivery.com/accounts/USSSA/bulletins/42e75c3 (saved: `sources/ssa-release.txt`)

| Claim in the script | Words on the page |
|---|---|
| 3.6% increase for 2027 | "today announced a 3.6 percent benefit increase for 2027" |
| Average +$75 a month | "On average, Social Security retirement benefits will increase by $75 per month." |
| Nearly 72 million, from January 2027 | "Nearly 72 million Social Security beneficiaries will see a 3.6 percent cost-of-living adjustment (COLA) beginning in January 2027." |
| One-page notice with exact dates, dollar amounts, deductions | "a simplified, one-page COLA notice ... provides exact dates and dollar amounts of an individual's new benefit amount and any deductions" |
| Online in late November, up to three weeks before paper | "can view their COLA notice online starting in late November—up to three weeks earlier than receiving a paper notice in the mail" |
| Paperless enrolment by November 18 | "will need to create one and enroll in paperless notices by November 18 to see their COLA notice online" |
| By mail in December otherwise | "will receive their COLA notice by mail in December" |
| Medicare premium amount arrives in the same place | "For Medicare enrollees, the 2027 premium amount will be available via my Social Security Message Center starting in late November." |

## Source 2: Federal Register notice, October 26, 2026
Social Security Administration, "Cost-of-Living Increase and Other Determinations for 2027".
https://www.govinfo.gov/content/pkg/FR-2026-10-26/html/2026-21796.htm (saved: `sources/federal-register-2027.txt`)

| Claim in the script | Words in the notice |
|---|---|
| Earnings limit $2,130 a month, $25,560 a year | "the lower retirement earnings test monthly exempt amount is $2,130 for 2027. The lower annual exempt amount is $25,560" |
| 2026 limit $24,480 | "the 2026 monthly exempt amount ($2,040)"; 12 x $2,040 = $24,480 |
| Limit in the year of full retirement age $67,920 | "the higher retirement earnings test monthly exempt amount is $5,660 for 2027. The higher annual exempt amount is $67,920" |
| 2026 higher limit $65,160 | "the 2026 monthly exempt amount ($5,430)"; 12 x $5,430 = $65,160 |
| $1 withheld per $2; $1 per $3 in the year of full retirement age, months before it only | "For beneficiaries who attain NRA in the year, we withhold $1 in benefits for every $3 of earnings over the annual exempt amount for months before NRA. For all other beneficiaries under NRA, we withhold $1 in benefits for every $2" |
| Tax ceiling $192,300, up from $184,500 | "Because $192,300 exceeds the current base amount of $184,500, the OASDI contribution and benefit base is $192,300 for 2027." |
| The ceiling also caps earnings counted for benefits | "It is also the maximum annual earnings used in determining a person's OASDI benefits." |
| Credit: $1,970, up from $1,890 | "Because $1,970 exceeds the current amount of $1,890, the quarter of coverage amount is $1,970 for 2027." |
| Average wage index for 2025: $72,800 | "The national average wage index for 2025 is $72,800.33." |
| The three amounts are calculated from the wage index | "This index affects the following amounts: (1) The ... contribution and benefit base ... (2) The monthly exempt amounts under the OASDI retirement earnings test ... (5) The taxable earnings a person must have in 2027 to be credited with a quarter of coverage" |

## Source 3: Code of Federal Regulations, title 20, part 404 (eCFR API, text as of June 1, 2026)
Saved: `sources/cfr-404.*.txt`. The eCFR website refuses automated browsers, so these facts are shown on cards, not as page screenshots.

| Claim in the script | Section and words |
|---|---|
| Full retirement age: 66 and 10 months if born in 1959, 67 if born in 1960 or later | 404.409(a): "1/2/1959—1/1/1960 66 years and 10 months. 1/2/1960 and later 67 years." |
| No limit from the month of full retirement age | 404.435(a)(3): "We will not reduce your benefits on account of excess earnings for any month in which you ... Were at full retirement age" |
| Earnings are wages plus net self-employment earnings | 404.429(a): "the sum of your wages for services rendered in a taxable year, plus your net earnings from self-employment" |
| Grace year: a month under the monthly limit, with no self-employment work, is paid | 404.435(a)(7), (b): "Had a non-service month in your grace year ... A non-service month is any month in which you ... Do not work in self-employment ... Do not perform services for wages greater than the monthly exempt amount" |
| Withheld months are credited back at full retirement age | 404.412(a)(1), (b): "Months subject to deduction under § 404.415 ... We make automatic adjustments in benefits ... Increases in benefit amounts based upon this adjustment are effective with the month of attainment of full retirement age." |
| A worker's excess earnings also reduce a spouse's or child's benefits on that record | 404.415(b): "We will reduce husband's, wife's, and child's insurance benefits payable ... on the insured individual's earnings record because of the excess earnings of the insured individual." |
| Withholding is based on estimated earnings, from the start of the year | 404.434(a): "if your estimated earnings for a year result in estimated excess earnings ... we will charge these excess earnings to your full benefit each month from the beginning of the year" |
| At most four credits a year, from total wages and self-employment income in the year | 404.143(a): "we cannot credit you with more than four QCs for any calendar year"; "for each part of the total wages paid and self-employment income credited ... in a calendar year" |
| 40 credits for someone reaching 62 now | 404.110(b): "not more than 40 QCs to be fully insured"; "one QC ... for each calendar year elapsing after ... the year in which you became age 21, and before ... The year you become age 62" (40 years) |

## Source 4: IRS
https://www.irs.gov/taxtopics/tc751 (saved: `sources/irs-topic-751.txt`), https://www.irs.gov/taxtopics/tc608 (saved: `sources/irs-topic-608.txt`)

| Claim in the script | Words on the page |
|---|---|
| 6.2% employee, 6.2% employer | "The current tax rate for Social Security is 6.2% for the employer and 6.2% for the employee" |
| With more than one employer, the total withheld can exceed the maximum; the excess may be claimed as a credit | "If you had more than one employer and too much Social Security tax ... withheld, you may be able to claim the excess as a credit against your income tax on your income tax return." |

## Arithmetic (ours)
- $2,000 x 3.6% = $72.
- $35,560 - $25,560 = $10,000 over; half withheld = $5,000.
- $73,920 - $67,920 = $6,000 over; one third withheld = $2,000.
- $192,300 - $184,500 = $7,800.
- $184,500 x 6.2% = $11,439.00. $192,300 x 6.2% = $11,922.60. Difference $483.60.
- 4 x $1,970 = $7,880. 4 x $1,890 = $7,560. Difference $320.
- 40 credits at 4 a year = 10 years. 10 credits at 4 a year = 2.5 years.

## Statements with no number that rest on general knowledge
- The earnings record is visible in a my Social Security account.
- A Social Security pay-stub line stops once pay passes the ceiling (follows from the ceiling being "the maximum annual earnings on which OASDI taxes are paid").
