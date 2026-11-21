import React from "react";
import { AccentColor } from "../theme";

export const AccentContext = React.createContext<AccentColor>("red");

export const useAccent = (): AccentColor => React.useContext(AccentContext);
