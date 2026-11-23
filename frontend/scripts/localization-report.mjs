import fs from 'node:fs';
import { Buffer } from 'node:buffer';
import process from 'node:process';
import ts from 'typescript';
const inventory = JSON.parse(fs.readFileSync('src/localization-inventory.json', 'utf8'));
for (const file of Object.keys(inventory)) {
  const source = ts.createSourceFile(
    file,
    fs.readFileSync(`src/${file}.tsx`, 'utf8'),
    ts.ScriptTarget.Latest,
    true,
    ts.ScriptKind.TSX,
  );
  const keys = new Set(inventory[file]);
  function visit(node) {
    if (
      ts.isCallExpression(node) &&
      node.expression.getText(source) === 'tr' &&
      node.arguments[0] &&
      ts.isStringLiteral(node.arguments[0]) &&
      node.arguments[0].text.trim()
    )
      keys.add(node.arguments[0].text.trim());
    ts.forEachChild(node, visit);
  }
  visit(source);
  inventory[file] = [...keys].sort();
}
fs.writeFileSync('src/localization-inventory.json', JSON.stringify(inventory, null, 2) + '\n');
const code = ts.transpileModule(fs.readFileSync('src/translations.ts', 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
}).outputText;
const { translations } = await import(
  `data:text/javascript;base64,${Buffer.from(code).toString('base64')}`
);
const pages = Object.fromEntries(
  Object.entries(inventory).map(([page, keys]) => {
    const missing = keys.filter((key) => !translations[key.trim()]);
    return [page, { phrases: keys.length, translated: keys.length - missing.length, missing }];
  }),
);
const unique = [...new Set(Object.values(inventory).flat())];
const report = {
  method:
    'Unique static JSX phrases captured before instrumentation, excluding official/dynamic data. Translation means dictionary coverage, not native-language certification.',
  dictionary_entries: Object.keys(translations).length,
  static_phrases: unique.length,
  covered: unique.filter((key) => translations[key.trim()]).length,
  pages,
};
fs.writeFileSync('../docs/LOCALIZATION_COVERAGE.json', JSON.stringify(report, null, 2) + '\n');
process.stdout.write(
  JSON.stringify(
    {
      ...report,
      pages: Object.fromEntries(
        Object.entries(pages).map(([page, data]) => [
          page,
          { phrases: data.phrases, translated: data.translated },
        ]),
      ),
    },
    null,
    2,
  ) + '\n',
);
