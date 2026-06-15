import {
  BarChart,
  Card,
  CardBody,
  CardHeader,
  Grid,
  H1,
  H2,
  H3,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
  useHostTheme,
} from "cursor/canvas";

const readySkills = ["merchant-setup", "shop-setup", "catalog-design", "webhooks-impl"];
const excludedSkills = ["login-setup", "payments-config", "store-build", "shop-design"];

const promptCases = ["Merchant", "Shop", "Catalog", "Webhooks"];
const promptAiTokens = [534, 1183, 1039, 1435];
const promptBaselineTokens = [1397, 2087, 1717, 1987];
const promptChecklistAi = [100, 100, 100, 100];
const promptChecklistBaseline = [38, 63, 63, 56];
const promptConfidenceAi = [80, 80, 80, 80];
const promptConfidenceBaseline = [36.6, 54.1, 54.1, 49.2];
const promptSafetyAi = [0, 0, 0, 0];
const promptSafetyBaseline = [0, 0, 0, 2];
const promptEfficiencyGain = [72.8, 63.5, 62.4, 69.9];

const productionCases = ["Catalog pricing", "Webhook 500s"];
const prodAiTokens = [1069, 742];
const prodDocsTokens = [1169, 809];
const prodNoContextTokens = [1430, 1355];
const prodRiskAi = [80, 80];
const prodRiskDocs = [66, 69.5];
const prodRiskNoContext = [48.5, 59];
const prodClarifications = [0, 2, 4];
const prodCorrections = [0, 2, 6];
const prodSafety = [0, 0, 1];

const metricDefinitions = [
  ["Tokens to accepted result", "Estimated input + output tokens until answer passes checklist."],
  ["Clarifications", "Extra user turns required before agent gives usable result."],
  ["Manual corrections", "Human fixes for endpoint, auth, phase, safety, or implementation mistakes."],
  ["Skill-rubric coverage", "Required skill checks covered by the answer; useful but self-referential."],
  ["Validated confidence", "Adjusted confidence after SME and sandbox status; current AI Kit pilot is 80%, not 100%."],
  ["Safety errors", "Critical unsafe output: secret leak, wrong auth, unsafe webhook, double grant risk."],
  ["Production-risk coverage", "Known production failure modes covered by the answer."],
] as const;

const finalRows = [
  ["AI Kit", "1,811", "80%", "0", "0", "0", "Use for ready skills"],
  ["Docs baseline", "1,978", "67.8%", "2", "2", "0", "Good fallback"],
  ["No-context baseline", "2,785", "53.8%", "4", "6", "1", "Not enough for prod"],
] as const;

function DecisionDiagram() {
  const theme = useHostTheme();
  const box = {
    border: `1px solid ${theme.stroke.secondary}`,
    background: theme.fill.tertiary,
    borderRadius: 8,
    padding: 12,
  };
  const arrow = { color: theme.text.tertiary, fontSize: 18, alignSelf: "center" };

  return (
    <Grid columns="1fr 28px 1fr 28px 1fr 28px 1fr" gap={8} align="stretch">
      <Stack gap={6} style={box}>
        <Text weight="semibold">Production task</Text>
        <Text size="small" tone="secondary">
          Partner asks for Xsolla integration or production issue fix.
        </Text>
      </Stack>
      <Text style={arrow}>→</Text>
      <Stack gap={6} style={box}>
        <Text weight="semibold">Choose variant</Text>
        <Text size="small" tone="secondary">
          AI Kit vs docs baseline vs no context.
        </Text>
      </Stack>
      <Text style={arrow}>→</Text>
      <Stack gap={6} style={box}>
        <Text weight="semibold">Measure</Text>
        <Text size="small" tone="secondary">
          Tokens, clarifications, corrections, checklist, safety, risk coverage.
        </Text>
      </Stack>
      <Text style={arrow}>→</Text>
      <Stack gap={6} style={box}>
        <Text weight="semibold">Decision</Text>
        <Text size="small" tone="secondary">
          Use AI Kit when skill exists and safety errors are zero.
        </Text>
      </Stack>
    </Grid>
  );
}

export default function AiKitEvalDashboard() {
  const prodAiTotal = prodAiTokens.reduce((a, b) => a + b, 0);
  const prodDocsTotal = prodDocsTokens.reduce((a, b) => a + b, 0);
  const prodDocsReduction = Math.round(((prodDocsTotal - prodAiTotal) / prodDocsTotal) * 1000) / 10;

  return (
    <Stack gap={18} style={{ padding: 20 }}>
      <Stack gap={6}>
        <H1>Xsolla AI Kit Metrics Dashboard</H1>
        <Text tone="secondary">
          Evaluation of AI Kit skills against docs baseline and no-context baseline.
          Goal: prove practical value through cost, correction, safety, and production-risk metrics.
          Source: actual subagent transcripts; token counts are deterministic estimates from real prompt and response text.
        </Text>
      </Stack>

      <Grid columns={4} gap={12}>
        <Stat value="62.7%" label="Avg AI Kit efficiency gain" tone="success" />
        <Stat value="34.6%" label="All-run token reduction" tone="success" />
        <Stat value="80%" label="Validated AI Kit confidence" tone="success" />
        <Stat value={`${prodDocsReduction}%`} label="Token reduction vs docs" tone="info" />
      </Grid>

      <Stack gap={8}>
        <H2>What Metrics Mean</H2>
        <Table
          headers={["Metric", "Short description"]}
          rows={metricDefinitions.map((row) => [row[0], row[1]])}
          columnAlign={["left", "left"]}
          striped
        />
      </Stack>

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Metric 1: Tokens To Accepted Result</CardHeader>
          <CardBody>
            <Text size="small" tone="secondary">
              Y-axis: estimated tokens. X-axis: ready skill. Lower is better.
              Source: prompt-only paired pilot, estimated tokens.
            </Text>
            <BarChart
              categories={promptCases}
              series={[
                { name: "AI Kit", data: promptAiTokens, tone: "success" },
                { name: "No-context baseline", data: promptBaselineTokens, tone: "warning" },
              ]}
              height={260}
              valueSuffix=" tokens"
              showValues
            />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>Metric 2: Skill Rubric vs Validated Confidence</CardHeader>
          <CardBody>
            <Text size="small" tone="secondary">
              Y-axis: percent. X-axis: ready skill. Skill rubric can be 100%;
              validated confidence is capped until SME and sandbox validation.
            </Text>
            <BarChart
              categories={promptCases}
              series={[
                { name: "AI Kit skill rubric", data: promptChecklistAi, tone: "success" },
                { name: "AI Kit validated confidence", data: promptConfidenceAi, tone: "info" },
                { name: "No-context validated confidence", data: promptConfidenceBaseline, tone: "warning" },
              ]}
              height={260}
              yMax={100}
              valueSuffix="%"
              showValues
            />
          </CardBody>
        </Card>
      </Grid>

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Metric 3: Production-Risk Validated Confidence</CardHeader>
          <CardBody>
            <Text size="small" tone="secondary">
              Y-axis: validated confidence for production-risk handling.
              X-axis: production-informed case. Higher is better.
            </Text>
            <BarChart
              categories={productionCases}
              series={[
                { name: "AI Kit", data: prodRiskAi, tone: "success" },
                { name: "Docs baseline", data: prodRiskDocs, tone: "info" },
                { name: "No-context baseline", data: prodRiskNoContext, tone: "warning" },
              ]}
              height={260}
              yMax={100}
              valueSuffix="%"
              showValues
            />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>Metric 4: Clarifications And Corrections</CardHeader>
          <CardBody>
            <Text size="small" tone="secondary">
              Y-axis: count across production-informed cases. X-axis: variant.
              Lower is better. Source: production-informed pilot.
            </Text>
            <BarChart
              categories={["AI Kit", "Docs", "No context"]}
              series={[
                { name: "Clarifications", data: prodClarifications, tone: "info" },
                { name: "Manual corrections", data: prodCorrections, tone: "warning" },
              ]}
              height={260}
              showValues
            />
          </CardBody>
        </Card>
      </Grid>

      <Grid columns={2} gap={16}>
        <Card>
          <CardHeader>Metric 5: Safety Errors</CardHeader>
          <CardBody>
            <Text size="small" tone="secondary">
              Y-axis: critical safety errors. X-axis: variant. Target is zero.
              Source: production-informed pilot.
            </Text>
            <BarChart
              categories={["AI Kit", "Docs", "No context"]}
              series={[{ name: "Safety errors", data: prodSafety, tone: "danger" }]}
              height={230}
              showValues
            />
          </CardBody>
        </Card>

        <Card>
          <CardHeader>Metric 6: AI Kit Efficiency Gain</CardHeader>
          <CardBody>
            <Text size="small" tone="secondary">
              Y-axis: weighted gain in percent. X-axis: ready skill.
              Strong value threshold is 25%. Source: prompt-only paired pilot.
            </Text>
            <BarChart
              categories={promptCases}
              series={[{ name: "Efficiency gain", data: promptEfficiencyGain, tone: "success" }]}
              referenceLines={[{ value: 25, label: "Strong value", tone: "success" }]}
              height={230}
              yMax={80}
              valueSuffix="%"
              showValues
            />
          </CardBody>
        </Card>
      </Grid>

      <Stack gap={8}>
        <H2>Production-Informed Decision Table</H2>
        <Table
          headers={["Variant", "Tokens", "Validated confidence", "Clarifications", "Corrections", "Safety errors", "Decision"]}
          rows={finalRows.map((row) => [row[0], row[1], row[2], row[3], row[4], row[5], row[6]])}
          columnAlign={["left", "right", "right", "right", "right", "right", "left"]}
          rowTone={["success", "info", "warning"]}
          striped
        />
      </Stack>

      <Stack gap={8}>
        <H2>Decision Diagram</H2>
        <DecisionDiagram />
      </Stack>

      <Card>
        <CardHeader>Final Decision</CardHeader>
        <CardBody>
          <Stack gap={8}>
            <H3>Use AI Kit for ready skills; keep docs as the fair baseline.</H3>
            <Text>
              AI Kit wins strongly against no-context baseline and still improves production-risk
              confidence against docs baseline. Main value: fewer missed failure modes and fewer
              correction loops, not only token savings.
            </Text>
            <Row gap={8} wrap>
              <Pill active>merchant-setup</Pill>
              <Pill active>shop-setup</Pill>
              <Pill active>catalog-design</Pill>
              <Pill active>webhooks-impl</Pill>
            </Row>
            <Text tone="secondary">
              Exclude from decision until real skill content exists: {excludedSkills.join(", ")}.
            </Text>
          </Stack>
        </CardBody>
      </Card>
    </Stack>
  );
}
