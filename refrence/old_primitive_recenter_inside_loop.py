        # if type(primitive) == gerber.primitives.Line:
        #     self.primitives[ind].start = (primitive.start[0] + x_offset, primitive.start[1] + y_offset)
        #     self.primitives[ind].end = (primitive.end[0] + x_offset, primitive.end[1] + y_offset)

        # elif type(primitive) == gerber.primitives.Region:
        #     for ind2, region_primitive in enumerate(primitive.primitives):
        #         if type(region_primitive) == gerber.primitives.Line:
        #             self.primitives[ind].primitives[ind2].start = (region_primitive.start[0] + x_offset, region_primitive.start[1] + y_offset)
        #             self.primitives[ind].primitives[ind2].end = (region_primitive.end[0] + x_offset, region_primitive.end[1] + y_offset)

        #         else:
        #             # Assuming all primitives inside Region object is line
        #             raise NotImplementedError(f"I thought all primitives inside a Region object is Line primitives only, found {type(primitive)}")

        # elif type(primitive) == gerber.primitives.Arc:
        #     primitive.offset(x_offset, y_offset)

        # else:
        #     # Check if this Gerber type is implemented
        #     try:
        #         tmp = GerberToShapely(primitive)
        #     except NotImplementedError:
        #         print(f"\nThis Gerber Object {type(primitive)} isn't implemented how to recenter!\n\n")
        #         raise

        #     self.primitives[ind].position = (primitive.position[0] + x_offset, primitive.position[1] + y_offset)



