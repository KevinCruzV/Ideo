declare module "*.ttf" {
  const url: string;
  export default url;
}

declare module "*.png" {
  const url: string;
  export default url;
}

declare const require: {
  context(
    directory: string,
    deep: boolean,
    filter: RegExp,
  ): {
    (key: string): string;
    keys(): string[];
  };
};
