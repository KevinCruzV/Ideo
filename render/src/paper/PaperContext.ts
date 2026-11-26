import React from "react";
import type { Paper } from "./supports";

export const PaperContext = React.createContext<Paper>("creme");

export const usePaper = (): Paper => React.useContext(PaperContext);
