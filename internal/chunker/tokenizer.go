package chunker

import "github.com/tiktoken-go/tokenizer"

var enc tokenizer.Codec

func init() {
	var err error
	enc, err = tokenizer.Get(tokenizer.Cl100kBase)
	if err != nil {
		panic("failed to load cl100k_base tokenizer: " + err.Error())
	}
}

func countTokens(text string) int {
	ids, _, _ := enc.Encode(text)
	return len(ids)
}